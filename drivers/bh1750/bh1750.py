# Driver for the ROHM BH1750 ambient light sensor, the chip on GY-30 and GY-302 modules.
# Datasheet: https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf
#
# The chip has no registers: every setting is a one byte command, and a reading is two bytes,
# big endian, read straight off the bus.

from micropython import const

BH1750_ADDRESS = const(0x23)  # ADDR pin low or unconnected
BH1750_ADDRESS_HIGH = const(0x5C)  # ADDR pin high

# Measurement modes, all continuous.
CONTINUOUS_HIGH = const(0x10)  # 1 lux steps, 120ms
CONTINUOUS_HIGH_2 = const(0x11)  # 0.5 lux steps, 120ms
CONTINUOUS_LOW = const(0x13)  # 4 lux steps, 16ms

_POWER_ON = const(0x01)
_MTREG_DEFAULT = const(69)
_MODES = (CONTINUOUS_HIGH, CONTINUOUS_HIGH_2, CONTINUOUS_LOW)


class BH1750:
    """A BH1750 on `i2c`, reading ambient light in lux.

    `mtreg` is the measurement time register, 31 to 254. Higher is more sensitive and slower,
    lower reaches brighter light. `accuracy` is the datasheet's counts per lux, typically 1.2 but
    anywhere from 0.96 to 1.44 on a given chip: the knob to calibrate against a light meter.
    """

    # ponytail: settings are fixed at construction, and one-shot modes are not used. Add them
    # when a battery project needs the chip to power down between readings.
    def __init__(
        self,
        i2c,
        address=BH1750_ADDRESS,
        mode=CONTINUOUS_HIGH,
        mtreg=_MTREG_DEFAULT,
        accuracy=1.2,
    ):
        if mode not in _MODES:
            raise ValueError("Use one of the CONTINUOUS_ constants")
        if not 31 <= mtreg <= 254:
            raise ValueError("mtreg must be between 31 and 254")
        self.i2c = i2c
        self.address = address
        self.mode = mode
        self.mtreg = mtreg
        self.accuracy = accuracy
        try:
            self._command(_POWER_ON)
            # The measurement time is split over two commands: the top two bits, then the low six.
            self._command(0x40 | (mtreg >> 6))
            self._command(0xB8 | (mtreg & 0x3F))
            self._command(mode)
        except OSError:
            raise OSError("No BH1750 at 0x%02x" % address)

    def _command(self, command):
        self.i2c.writeto(self.address, bytes((command,)))

    @property
    def light(self):
        """The raw 16 bit count. 65535 means the sensor is saturated."""
        high, low = self.i2c.readfrom(self.address, 2)
        return (high << 8) | low

    @property
    def lux(self):
        """Ambient light in lux, scaled for the mode and measurement time in use."""
        lux = self.light / self.accuracy * _MTREG_DEFAULT / self.mtreg
        return lux / 2 if self.mode == CONTINUOUS_HIGH_2 else lux
