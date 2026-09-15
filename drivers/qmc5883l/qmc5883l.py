# Driver for the QST QMC5883L three axis magnetometer, the chip on HW-246 and most recent GY-271
# compass modules.
# Datasheet: https://datasheet.lcsc.com/lcsc/QST-QMC5883L-TR_C192585.pdf
#
# Readings are 16 bit signed words, little endian, in X, Y, Z order.

from math import atan2, degrees
from micropython import const
from struct import unpack

QMC5883L_ADDRESS = const(0x0D)

# Field range. 2 gauss has four times finer steps and still fits the earth's roughly 0.5 gauss,
# but a nearby magnet or motor overflows it sooner.
RANGE_2G = const(0x00)
RANGE_8G = const(0x10)

# Output data rate.
RATE_10HZ = const(0x00)
RATE_50HZ = const(0x04)
RATE_100HZ = const(0x08)
RATE_200HZ = const(0x0C)

# Oversampling. More is less noisy and draws more current.
OVERSAMPLE_512 = const(0x00)
OVERSAMPLE_256 = const(0x40)
OVERSAMPLE_128 = const(0x80)
OVERSAMPLE_64 = const(0xC0)

_DATA = const(0x00)
_STATUS = const(0x06)
_CONTROL = const(0x09)
_SET_RESET = const(0x0B)
_CONTINUOUS = const(0x01)

_COUNTS_PER_GAUSS = {RANGE_2G: 12000.0, RANGE_8G: 3000.0}
_RATES = (RATE_10HZ, RATE_50HZ, RATE_100HZ, RATE_200HZ)
_OVERSAMPLES = (OVERSAMPLE_512, OVERSAMPLE_256, OVERSAMPLE_128, OVERSAMPLE_64)
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


class QMC5883L:
    """A QMC5883L on `i2c`, measuring the magnetic field in microtesla.

    `offset` is the hard iron correction in microtesla, subtracted from every reading, and
    `scale` the soft iron correction multiplied in afterwards. Both come from calibrate().
    """

    # ponytail: settings are fixed at construction. Make a new instance to change them.
    def __init__(
        self,
        i2c,
        address=QMC5883L_ADDRESS,
        field_range=RANGE_8G,
        rate=RATE_200HZ,
        oversample=OVERSAMPLE_512,
        offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
    ):
        if field_range not in _COUNTS_PER_GAUSS:
            raise ValueError("Use one of the RANGE_ constants")
        if rate not in _RATES:
            raise ValueError("Use one of the RATE_ constants")
        if oversample not in _OVERSAMPLES:
            raise ValueError("Use one of the OVERSAMPLE_ constants")
        self.i2c = i2c
        self.address = address
        self.offset = offset
        self.scale = scale
        self._counts_per_gauss = _COUNTS_PER_GAUSS[field_range]
        try:
            # The set/reset period register is barely documented but has to be 0x01 or readings
            # drift.
            i2c.writeto_mem(address, _SET_RESET, b"\x01")
            control = oversample | field_range | rate | _CONTINUOUS
            i2c.writeto_mem(address, _CONTROL, bytes((control,)))
        except OSError:
            raise OSError("No QMC5883L at 0x%02x" % address)

    def _status(self):
        return self.i2c.readfrom_mem(self.address, _STATUS, 1)[0]

    @property
    def ready(self):
        """True once a fresh sample is waiting."""
        return bool(self._status() & 0x01)

    @property
    def overflow(self):
        """True when an axis went past the range, so the reading is clipped. Try RANGE_8G."""
        return bool(self._status() & 0x02)

    def _field(self):
        """Uncalibrated (x, y, z) in microtesla."""
        counts = unpack("<hhh", self.i2c.readfrom_mem(self.address, _DATA, 6))
        return tuple(count / self._counts_per_gauss * _GAUSS_TO_MICROTESLA for count in counts)

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
