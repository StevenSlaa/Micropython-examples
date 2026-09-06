# Driver for the Vishay VCNL4040 proximity and ambient light sensor.
# Datasheet: https://www.vishay.com/docs/84274/vcnl4040.pdf
#
# Every register is a 16 bit word, little endian, at an 8 bit command code. Several of them
# hold two independent 8 bit configuration registers, one per byte.

from micropython import const

VCNL4040_ADDRESS = const(0x60)

# Ambient light integration time. Longer is more sensitive and slower.
ALS_80MS = const(0x00)
ALS_160MS = const(0x01)
ALS_320MS = const(0x02)
ALS_640MS = const(0x03)

# Infrared LED drive current. More current reaches further and costs more power.
LED_50MA = const(0x00)
LED_75MA = const(0x01)
LED_100MA = const(0x02)
LED_120MA = const(0x03)
LED_140MA = const(0x04)
LED_160MA = const(0x05)
LED_180MA = const(0x06)
LED_200MA = const(0x07)

# LED duty cycle: how often the sensor pulses it.
DUTY_1_40 = const(0x00)
DUTY_1_80 = const(0x01)
DUTY_1_160 = const(0x02)
DUTY_1_320 = const(0x03)

_ALS_CONF = const(0x00)
_PS_CONF1_CONF2 = const(0x03)
_PS_CONF3_MS = const(0x04)
_PS_CANCELLATION = const(0x05)
_PS_DATA = const(0x08)
_ALS_DATA = const(0x09)
_WHITE_DATA = const(0x0A)
_DEVICE_ID = const(0x0C)

_LUX_PER_STEP = 0.1  # at the 80ms integration time; each longer step halves it


class VCNL4040:
    """A VCNL4040 on `i2c`, reading proximity and ambient light.

    Proximity is a bare number, not a distance: it rises as something comes closer, and how
    fast depends on the LED settings and on what the object is. Ambient light is real lux.
    """

    def __init__(
        self,
        i2c,
        address=VCNL4040_ADDRESS,
        integration_time=ALS_80MS,
        led_current=LED_200MA,
        duty=DUTY_1_40,
        high_resolution=False,
    ):
        self.i2c = i2c
        self.address = address
        if self._read(_DEVICE_ID) != 0x0186:
            raise OSError("No VCNL4040 at 0x%02x" % address)
        self._integration_time = integration_time
        # Ambient light on, interrupts off.
        self._write(_ALS_CONF, integration_time << 6)
        # PS_CONF1: duty cycle and 8T integration, proximity on. PS_CONF2: output width.
        proximity_config = (duty << 6) | (0x07 << 1)  # 8T integration, proximity enabled
        if high_resolution:
            proximity_config |= 0x08 << 8  # PS_CONF2: 16 bit output instead of 12
        self._write(_PS_CONF1_CONF2, proximity_config)
        # PS_CONF3 left at its defaults; PS_MS carries the LED current, and its top bit turns
        # the white channel off, so leaving it clear keeps white readings available.
        self._write(_PS_CONF3_MS, led_current << 8)

    def _read(self, register):
        return int.from_bytes(self.i2c.readfrom_mem(self.address, register, 2), "little")

    def _write(self, register, value):
        self.i2c.writeto_mem(self.address, register, (value & 0xFFFF).to_bytes(2, "little"))

    @property
    def proximity(self):
        """Rises as an object approaches: roughly 0 in clear air, thousands against a hand."""
        return self._read(_PS_DATA)

    @property
    def light(self):
        """The raw ambient light count, which changes meaning with the integration time."""
        return self._read(_ALS_DATA)

    @property
    def lux(self):
        """Ambient light in lux, scaled for the integration time in use."""
        return self._read(_ALS_DATA) * (_LUX_PER_STEP / (1 << self._integration_time))

    @property
    def white(self):
        """The white light channel, which unlike lux also responds to infrared."""
        return self._read(_WHITE_DATA)

    @property
    def integration_time(self):
        """One of the ALS_ constants. Longer sees dimmer light and updates more slowly."""
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        if value not in (ALS_80MS, ALS_160MS, ALS_320MS, ALS_640MS):
            raise ValueError("Use one of the ALS_ constants")
        self._integration_time = value
        self._write(_ALS_CONF, (self._read(_ALS_CONF) & ~0xC0) | (value << 6))

    @property
    def led_current(self):
        """One of the LED_ constants."""
        return (self._read(_PS_CONF3_MS) >> 8) & 0x07

    @led_current.setter
    def led_current(self, value):
        register = self._read(_PS_CONF3_MS) & ~(0x07 << 8)
        self._write(_PS_CONF3_MS, register | ((value & 0x07) << 8))

    @property
    def cancellation(self):
        """A constant subtracted from every proximity reading, 0 to 65535.

        Cover glass reflects some of the LED straight back, so a mounted sensor reads a few
        hundred with nothing in front of it. Read `proximity` with the view clear and set this
        to what you saw, and clear air becomes zero again.
        """
        return self._read(_PS_CANCELLATION)

    @cancellation.setter
    def cancellation(self, value):
        self._write(_PS_CANCELLATION, value)
