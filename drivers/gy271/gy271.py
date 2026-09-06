# Driver for the GY-271 / HW-246 compass module, which carries either a QMC5883L or an
# HMC5883L. The two chips share a footprint and nothing else: different address, different
# byte order, different axis order.
#
# QMC5883L datasheet: https://datasheet.lcsc.com/lcsc/QST-QMC5883L-TR_C192585.pdf
# HMC5883L datasheet: https://cdn-shop.adafruit.com/datasheets/HMC5883L_3-Axis_Digital_Compass_IC.pdf

from math import atan2, degrees
from micropython import const
from struct import unpack

QMC5883L_ADDRESS = const(0x0D)
HMC5883L_ADDRESS = const(0x1E)
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


class _Magnetometer:
    """Scaling, calibration and heading maths shared by both chips.

    `offset` is the hard iron correction in microtesla, subtracted from every reading, and
    `scale` the soft iron correction multiplied in afterwards. Both come from calibrate().
    """

    ADDRESS = 0
    COUNTS_PER_GAUSS = 1.0

    def __init__(self, i2c, address=None, offset=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
        self.i2c = i2c
        self.address = self.ADDRESS if address is None else address
        self.offset = offset
        self.scale = scale
        self._configure()

    def _configure(self):
        raise NotImplementedError

    def _counts(self):
        raise NotImplementedError

    def _field(self):
        """Uncalibrated (x, y, z) in microtesla."""
        return tuple(
            count / self.COUNTS_PER_GAUSS * _GAUSS_TO_MICROTESLA for count in self._counts()
        )

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

        A magnetometer reads the magnet in your speaker and the steel in your desk as well as
        the earth, so an uncalibrated heading can be tens of degrees out. Keep the returned
        offset and scale and pass them to the constructor next time.
        """
        # Imported here so the module itself stays importable anywhere.
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


class QMC5883L(_Magnetometer):
    """The QST chip, which is what an HW-246 and most recent GY-271 boards carry."""

    ADDRESS = QMC5883L_ADDRESS
    COUNTS_PER_GAUSS = 3000.0  # the 8 gauss range set below

    def _configure(self):
        # The set/reset period register is undocumented but has to be 0x01 or readings drift.
        self.i2c.writeto_mem(self.address, 0x0B, b"\x01")
        # Continuous, 200Hz, 8 gauss, 512x oversampling.
        self.i2c.writeto_mem(self.address, 0x09, b"\x1d")

    @property
    def ready(self):
        """True once a fresh sample is waiting."""
        return bool(self.i2c.readfrom_mem(self.address, 0x06, 1)[0] & 0x01)

    def _counts(self):
        return unpack("<hhh", self.i2c.readfrom_mem(self.address, 0x00, 6))


class HMC5883L(_Magnetometer):
    """The older Honeywell chip, on boards labelled GY-271 with a 0x1e address."""

    ADDRESS = HMC5883L_ADDRESS
    COUNTS_PER_GAUSS = 1090.0  # the +-1.3 gauss gain set below

    def _configure(self):
        self.i2c.writeto_mem(self.address, 0x00, b"\x70")  # 8 samples averaged, 15Hz
        self.i2c.writeto_mem(self.address, 0x01, b"\x20")  # +-1.3 gauss
        self.i2c.writeto_mem(self.address, 0x02, b"\x00")  # continuous measurement

    def _counts(self):
        # The registers run X, Z, Y, big endian. Getting this wrong is why a compass can look
        # like it works until you tilt it.
        x, z, y = unpack(">hhh", self.i2c.readfrom_mem(self.address, 0x03, 6))
        return x, y, z


def compass(i2c, **kwargs):
    """Returns a driver for whichever chip the module in front of you actually carries."""
    found = i2c.scan()
    if QMC5883L_ADDRESS in found:
        return QMC5883L(i2c, **kwargs)
    if HMC5883L_ADDRESS in found:
        return HMC5883L(i2c, **kwargs)
    raise OSError("No QMC5883L (0x0d) or HMC5883L (0x1e) found on the I2C bus")
