# Driver for the Microchip TC74 digital temperature sensor (I2C).
# Datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/21462D.pdf

from micropython import const

_TEMP = const(0x00)  # read only, signed degrees Celsius
_CONFIG = const(0x01)  # bit 7 standby, bit 6 data ready
_STANDBY = const(0x80)
_READY = const(0x40)


class TC74:
    """A TC74 on `i2c`. The address is set by the part number: A0 is 0x48 up to A7 at 0x4F.

    The sensor resolves 1 degree and is accurate to about 2, so `offset` is there to trim it
    against a thermometer you trust.
    """

    def __init__(self, i2c, address=0x48, offset=0):
        self.i2c = i2c
        self.address = address
        self.offset = offset

    def _read(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    @property
    def temperature(self):
        """Degrees Celsius as a whole number, from -65 to 127."""
        value = self._read(_TEMP)
        return (value - 256 if value > 127 else value) + self.offset

    @property
    def ready(self):
        """False until the first conversion after power-up or waking has finished."""
        return bool(self._read(_CONFIG) & _READY)

    @property
    def standby(self):
        return bool(self._read(_CONFIG) & _STANDBY)

    @standby.setter
    def standby(self, value):
        """Standby drops the sensor to a few microamps, but freezes the temperature register."""
        config = self._read(_CONFIG)
        config = config | _STANDBY if value else config & ~_STANDBY
        self.i2c.writeto_mem(self.address, _CONFIG, bytes([config & 0xFF]))
