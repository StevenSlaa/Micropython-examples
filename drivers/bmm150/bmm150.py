# Driver for the Bosch BMM150 three axis geomagnetic sensor.
# Datasheet: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmm150-ds001.pdf
# Compensation from Bosch's BMM150 Sensor API: https://github.com/boschsensortec/BMM150_SensorAPI
# Copyright (c) 2020 Bosch Sensortec GmbH. All rights reserved. BSD-3-Clause.
#
# Unlike most magnetometers the raw counts are not a field strength. Every chip is trimmed at the
# factory, and a reading only means something after Bosch's compensation has combined it with
# those trim values and the chip's own resistance measurement (RHALL), taken with every sample.

from math import atan2, degrees
from micropython import const
from struct import unpack
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

BMM150_ADDRESS = const(0x10)

# Bosch's presets, as (XY, Z) repetition register values. More repetitions are less noisy, slower
# and draw more current.
LOW_POWER = (0x01, 0x02)
REGULAR = (0x04, 0x0E)
ENHANCED = (0x07, 0x1A)
HIGH_ACCURACY = (0x17, 0x52)  # too slow for more than RATE_20HZ

# Output data rate in normal mode. The codes are not in order.
RATE_2HZ = const(0x08)
RATE_6HZ = const(0x10)
RATE_8HZ = const(0x18)
RATE_10HZ = const(0x00)
RATE_15HZ = const(0x20)
RATE_20HZ = const(0x28)
RATE_25HZ = const(0x30)
RATE_30HZ = const(0x38)

_CHIP_ID = const(0x40)
_DATA = const(0x42)
_RHALL_LSB = const(0x48)
_POWER = const(0x4B)
_OP_MODE = const(0x4C)
_REP_XY = const(0x51)
_REP_Z = const(0x52)
_BMM150_ID = const(0x32)
_XY_OVERFLOW = const(-4096)
_Z_OVERFLOW = const(-16384)

_RATES = (RATE_2HZ, RATE_6HZ, RATE_8HZ, RATE_10HZ, RATE_15HZ, RATE_20HZ, RATE_25HZ, RATE_30HZ)
_NAN = float("nan")


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


class BMM150:
    """A BMM150 on `i2c`, measuring the magnetic field in microtesla.

    `offset` is the hard iron correction in microtesla, subtracted from every reading, and
    `scale` the soft iron correction multiplied in afterwards. Both come from calibrate().
    """

    # ponytail: settings are fixed at construction, and forced mode, interrupts and self test are
    # not used. Make a new instance to change the preset or rate.
    def __init__(
        self,
        i2c,
        address=BMM150_ADDRESS,
        preset=REGULAR,
        rate=RATE_10HZ,
        offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
    ):
        if rate not in _RATES:
            raise ValueError("Use one of the RATE_ constants")
        repetitions_xy, repetitions_z = preset
        self.i2c = i2c
        self.address = address
        self.offset = offset
        self.scale = scale
        try:
            # Out of power on the chip is suspended and answers nothing but the power bit.
            i2c.writeto_mem(address, _POWER, b"\x01")
            sleep_ms(3)
            chip_id = i2c.readfrom_mem(address, _CHIP_ID, 1)[0]
        except OSError:
            raise OSError("No BMM150 at 0x%02x. Boards use 0x10 to 0x13: try i2c.scan()" % address)
        if chip_id != _BMM150_ID:
            raise OSError("0x%02x is not a BMM150 (chip id 0x%02x)" % (address, chip_id))
        self._read_trim()
        i2c.writeto_mem(address, _REP_XY, bytes((repetitions_xy,)))
        i2c.writeto_mem(address, _REP_Z, bytes((repetitions_z,)))
        # Normal mode is 00 in the low bits, so the rate code is the whole register.
        i2c.writeto_mem(address, _OP_MODE, bytes((rate,)))

    def _read_trim(self):
        read = self.i2c.readfrom_mem
        self._x1, self._y1 = unpack("<bb", read(self.address, 0x5D, 2))
        self._z4, self._x2, self._y2 = unpack("<hbb", read(self.address, 0x62, 4))
        self._z2, self._z1, xyz1, self._z3, self._xy2, self._xy1 = unpack(
            "<hHHhbB", read(self.address, 0x68, 10)
        )
        self._xyz1 = xyz1 & 0x7FFF  # the top bit belongs to something else

    def _raw(self):
        """(x, y, z, rhall) counts. X and Y are 13 bit, Z 15 bit, RHALL 14 bit, all left aligned."""
        x, y, z, rhall = unpack("<hhhH", self.i2c.readfrom_mem(self.address, _DATA, 8))
        return x >> 3, y >> 3, z >> 1, rhall >> 2

    def _xy(self, raw, rhall, dig_1, dig_2):
        if raw == _XY_OVERFLOW or rhall == 0 or self._xyz1 == 0:
            return _NAN
        value = self._xyz1 * 16384.0 / rhall - 16384.0
        value = self._xy2 * (value * value / 268435456.0) + value * self._xy1 / 16384.0
        value = raw * ((value + 256.0) * (dig_2 + 160.0))
        return (value / 8192.0 + dig_1 * 8.0) / 16.0

    def _z(self, raw, rhall):
        if raw == _Z_OVERFLOW or rhall == 0 or self._z1 == 0 or self._z2 == 0 or self._xyz1 == 0:
            return _NAN
        numerator = (raw - self._z4) * 131072.0 - self._z3 * (rhall - self._xyz1)
        denominator = (self._z2 + self._z1 * rhall / 32768.0) * 4.0
        return numerator / denominator / 16.0

    def _field(self):
        """Uncalibrated (x, y, z) in microtesla. An axis that overflowed is nan."""
        x, y, z, rhall = self._raw()
        return (
            self._xy(x, rhall, self._x1, self._x2),
            self._xy(y, rhall, self._y1, self._y2),
            self._z(z, rhall),
        )

    @property
    def ready(self):
        """True once a fresh sample is waiting."""
        return bool(self.i2c.readfrom_mem(self.address, _RHALL_LSB, 1)[0] & 0x01)

    @property
    def magnetic(self):
        """Calibrated (x, y, z) field strength in microtesla. An axis that overflowed is nan."""
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
        low = [float("inf")] * 3
        high = [float("-inf")] * 3
        deadline = ticks_add(ticks_ms(), int(seconds * 1000))
        while ticks_diff(deadline, ticks_ms()) > 0:
            for axis, value in enumerate(self._field()):
                if value == value:  # nan is the one value not equal to itself: skip overflows
                    low[axis] = min(low[axis], value)
                    high[axis] = max(high[axis], value)
            sleep_ms(50)
        self.offset, self.scale = _correction(low, high)
        return self.offset, self.scale
