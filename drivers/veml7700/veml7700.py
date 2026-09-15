# Driver for the Vishay VEML7700 ambient light sensor.
# Datasheet: https://www.vishay.com/docs/84286/veml7700.pdf
#
# Every register is a 16 bit word, little endian, at an 8 bit command code.

from micropython import const

VEML7700_ADDRESS = const(0x10)

# Gain. Lower gain reaches brighter light with coarser steps.
GAIN_1 = const(0x00)
GAIN_2 = const(0x01)
GAIN_1_8 = const(0x02)
GAIN_1_4 = const(0x03)

# Integration time. Longer is more sensitive and slower. The codes are not in order.
IT_25MS = const(0x0C)
IT_50MS = const(0x08)
IT_100MS = const(0x00)
IT_200MS = const(0x01)
IT_400MS = const(0x02)
IT_800MS = const(0x03)

_ALS_CONF = const(0x00)
_ALS_DATA = const(0x04)
_WHITE_DATA = const(0x05)

_GAINS = {GAIN_1: 1.0, GAIN_2: 2.0, GAIN_1_8: 0.125, GAIN_1_4: 0.25}
_TIMES = {IT_25MS: 25, IT_50MS: 50, IT_100MS: 100, IT_200MS: 200, IT_400MS: 400, IT_800MS: 800}


class VEML7700:
    """A VEML7700 on `i2c`, reading ambient light in lux.

    `resolution` is lux per count at gain 2 and 800ms, the most sensitive setting; every other
    setting is scaled from it. Vishay's current documents give 0.0042, older ones 0.0036.
    """

    # ponytail: fixed gain and integration time, no auto-ranging. The default covers a dark room
    # to about 17 000 lux; add auto-ranging if one sensor has to read both night and full sun.
    def __init__(
        self,
        i2c,
        address=VEML7700_ADDRESS,
        gain=GAIN_1_4,
        integration_time=IT_100MS,
        resolution=0.0042,
    ):
        self.i2c = i2c
        self.address = address
        self.resolution = resolution
        if gain not in _GAINS:
            raise ValueError("Use one of the GAIN_ constants")
        if integration_time not in _TIMES:
            raise ValueError("Use one of the IT_ constants")
        self._gain = gain
        self._integration_time = integration_time
        try:
            self._configure()
        except OSError:
            raise OSError("No VEML7700 at 0x%02x" % address)

    def _configure(self):
        # The driver owns the whole register: interrupts off, persistence 1, and the shutdown bit
        # clear, which is what powers the sensor on. It starts up shut down.
        value = (self._gain << 11) | (self._integration_time << 6)
        self.i2c.writeto_mem(self.address, _ALS_CONF, value.to_bytes(2, "little"))

    def _read(self, register):
        return int.from_bytes(self.i2c.readfrom_mem(self.address, register, 2), "little")

    @property
    def light(self):
        """The raw ambient light count. 65535 means the sensor is saturated."""
        return self._read(_ALS_DATA)

    @property
    def white(self):
        """The raw white channel count, which unlike lux also responds to infrared."""
        return self._read(_WHITE_DATA)

    @property
    def lux(self):
        """Ambient light in lux, scaled for the gain and integration time in use."""
        # ponytail: linear, without the polynomial correction in older Vishay application notes.
        # That polynomial runs away above about 20 000 lux, giving millions in sunlight.
        return (
            self._read(_ALS_DATA)
            * self.resolution
            * (2.0 / _GAINS[self._gain])
            * (800 / _TIMES[self._integration_time])
        )

    @property
    def gain(self):
        """One of the GAIN_ constants."""
        return self._gain

    @gain.setter
    def gain(self, value):
        if value not in _GAINS:
            raise ValueError("Use one of the GAIN_ constants")
        self._gain = value
        self._configure()

    @property
    def integration_time(self):
        """One of the IT_ constants. A new reading takes this long to arrive after a change."""
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        if value not in _TIMES:
            raise ValueError("Use one of the IT_ constants")
        self._integration_time = value
        self._configure()
