# Driver for the Honeywell HMC5883L three axis magnetometer, the chip on older GY-271 compass
# modules.
# Datasheet: https://cdn-shop.adafruit.com/datasheets/HMC5883L_3-Axis_Digital_Compass_IC.pdf
#
# Readings are 16 bit signed words, big endian, in X, Z, Y order.

from math import atan2, degrees
from micropython import const
from struct import unpack

HMC5883L_ADDRESS = const(0x1E)

# Field range, bits 7:5 of configuration register B. The finer ranges resolve the earth's roughly
# 0.5 gauss better, but a nearby magnet or motor overflows them sooner.
RANGE_0_88G = const(0x00)
RANGE_1_3G = const(0x20)
RANGE_1_9G = const(0x40)
RANGE_2_5G = const(0x60)
RANGE_4G = const(0x80)
RANGE_4_7G = const(0xA0)
RANGE_5_6G = const(0xC0)
RANGE_8_1G = const(0xE0)

# Output data rate, bits 4:2 of configuration register A.
RATE_0_75HZ = const(0x00)
RATE_1_5HZ = const(0x04)
RATE_3HZ = const(0x08)
RATE_7_5HZ = const(0x0C)
RATE_15HZ = const(0x10)
RATE_30HZ = const(0x14)
RATE_75HZ = const(0x18)

# Samples averaged per reading, bits 6:5 of configuration register A. More is less noisy.
AVERAGE_1 = const(0x00)
AVERAGE_2 = const(0x20)
AVERAGE_4 = const(0x40)
AVERAGE_8 = const(0x60)

_CONFIG_A = const(0x00)
_CONFIG_B = const(0x01)
_MODE = const(0x02)
_DATA = const(0x03)
_STATUS = const(0x09)
_CONTINUOUS = const(0x00)
# What the chip writes into an axis that went past the range.
_OVERFLOW = const(-4096)

_COUNTS_PER_GAUSS = {
    RANGE_0_88G: 1370.0,
    RANGE_1_3G: 1090.0,
    RANGE_1_9G: 820.0,
    RANGE_2_5G: 660.0,
    RANGE_4G: 440.0,
    RANGE_4_7G: 390.0,
    RANGE_5_6G: 330.0,
    RANGE_8_1G: 230.0,
}
_RATES = (RATE_0_75HZ, RATE_1_5HZ, RATE_3HZ, RATE_7_5HZ, RATE_15HZ, RATE_30HZ, RATE_75HZ)
_AVERAGES = (AVERAGE_1, AVERAGE_2, AVERAGE_4, AVERAGE_8)
_GAUSS_TO_MICROTESLA = 100.0


def _correction(low, high):
    """Hard and soft iron correction from the extremes seen while turning the sensor.

    The offset centres each axis on zero; the scale evens out axes that swing less than the
    others, which is what tilted iron near the sensor does to a reading.
    """
    offset = tuple((high + low) / 2 for low, high in zip(low, high))
    spans = [(high - low) / 2 for low, high in zip(low, high)]
    average = sum(spans) / 3
    scale = tuple(average / span if span else 1.0 for span in spans)
    return offset, scale


class HMC5883L:
    """An HMC5883L on `i2c`, measuring the magnetic field in microtesla.

    `offset` is the hard iron correction in microtesla, subtracted from every reading, and
    `scale` the soft iron correction multiplied in afterwards. Both come from calibrate().
    """

    # ponytail: settings are fixed at construction. Make a new instance to change them.
    def __init__(
        self,
        i2c,
        address=HMC5883L_ADDRESS,
        field_range=RANGE_1_3G,
        rate=RATE_15HZ,
        average=AVERAGE_8,
        offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
    ):
        if field_range not in _COUNTS_PER_GAUSS:
            raise ValueError("Use one of the RANGE_ constants")
        if rate not in _RATES:
            raise ValueError("Use one of the RATE_ constants")
        if average not in _AVERAGES:
            raise ValueError("Use one of the AVERAGE_ constants")
        self.i2c = i2c
        self.address = address
        self.offset = offset
        self.scale = scale
        self.overflow = False
        self._counts_per_gauss = _COUNTS_PER_GAUSS[field_range]
        try:
            i2c.writeto_mem(address, _CONFIG_A, bytes((average | rate,)))
            i2c.writeto_mem(address, _CONFIG_B, bytes((field_range,)))
            i2c.writeto_mem(address, _MODE, bytes((_CONTINUOUS,)))
        except OSError:
            raise OSError("No HMC5883L at 0x%02x" % address)

    @property
    def ready(self):
        """True once a fresh sample is waiting."""
        return bool(self.i2c.readfrom_mem(self.address, _STATUS, 1)[0] & 0x01)

    def _field(self):
        """Uncalibrated (x, y, z) in microtesla. Sets `overflow` if an axis was clipped."""
        # The registers run X, Z, Y. Getting this wrong is why a compass can look like it works
        # until you tilt it.
        x, z, y = unpack(">hhh", self.i2c.readfrom_mem(self.address, _DATA, 6))
        self.overflow = _OVERFLOW in (x, y, z)
        return tuple(count / self._counts_per_gauss * _GAUSS_TO_MICROTESLA for count in (x, y, z))

    @property
    def magnetic(self):
        """Calibrated (x, y, z) field strength in microtesla."""
        return tuple(
            (value - offset) * scale
            for value, offset, scale in zip(self._field(), self.offset, self.scale)
        )

    def heading(self, declination=0.0):
        """Degrees clockwise from magnetic north, 0 to 360, with the board held flat.

        Pass your local magnetic declination to get true north instead.
        """
        x, y, _ = self.magnetic
        return (degrees(atan2(y, x)) + declination) % 360.0

    def calibrate(self, seconds=15):
        """Turn the module through every orientation, slowly, while this runs.

        Keep the returned offset and scale and pass them to the constructor next time.
        """
        # Imported here so the module itself stays importable on CPython for the test.
        from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

        low = list(self._field())
        high = list(low)
        deadline = ticks_add(ticks_ms(), int(seconds * 1000))
        while ticks_diff(deadline, ticks_ms()) > 0:
            for axis, value in enumerate(self._field()):
                low[axis] = min(low[axis], value)
                high[axis] = max(high[axis], value)
            sleep_ms(50)
        self.offset, self.scale = _correction(low, high)
        return self.offset, self.scale
