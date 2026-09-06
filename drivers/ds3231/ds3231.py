# Driver for the DS3231 real time clock, the module with the coin cell and the temperature
# compensated crystal. Datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/ds3231.pdf
#
# The chip keeps time in binary coded decimal: 0x59 means 59, not 89.

from micropython import const

DS3231_ADDRESS = const(0x68)

_SECONDS = const(0x00)
_CONTROL = const(0x0E)
_STATUS = const(0x0F)
_AGING_OFFSET = const(0x10)
_TEMPERATURE = const(0x11)
_OSF = const(0x80)  # status bit 7: the oscillator stopped, so the time is not to be trusted


def _from_bcd(value):
    return (value >> 4) * 10 + (value & 0x0F)


def _to_bcd(value):
    return ((value // 10) << 4) | (value % 10)


class DS3231:
    """A DS3231 on `i2c`.

    Times are 7-tuples of (year, month, day, hour, minute, second, weekday), with weekday 0 for
    Monday, so they line up with what `time.localtime()` gives you.
    """

    def __init__(self, i2c, address=DS3231_ADDRESS):
        self.i2c = i2c
        self.address = address

    def _read(self, register, length=1):
        return self.i2c.readfrom_mem(self.address, register, length)

    def _write(self, register, data):
        self.i2c.writeto_mem(self.address, register, bytes(data))

    @property
    def lost_power(self):
        """True when the clock has not been running, so whatever it reads is meaningless.

        Set on a module that has never been set, and on one whose battery went flat or was
        taken out. Setting the time clears it.
        """
        return bool(self._read(_STATUS)[0] & _OSF)

    @property
    def datetime(self):
        """(year, month, day, hour, minute, second, weekday)."""
        data = self._read(_SECONDS, 7)
        return (
            2000 + _from_bcd(data[6]),
            _from_bcd(data[5] & 0x1F),  # bit 7 is the century flag, not part of the month
            _from_bcd(data[4]),
            _from_bcd(data[2] & 0x3F),  # bits 6 and 7 are the 12/24 hour flags
            _from_bcd(data[1]),
            _from_bcd(data[0] & 0x7F),
            (_from_bcd(data[3]) - 1) % 7,
        )

    @datetime.setter
    def datetime(self, value):
        year, month, day, hour, minute, second = value[:6]
        weekday = value[6] if len(value) > 6 else 0
        self._write(
            _SECONDS,
            (
                _to_bcd(second),
                _to_bcd(minute),
                _to_bcd(hour),  # written with bit 6 clear, which is 24 hour mode
                _to_bcd(weekday + 1),
                _to_bcd(day),
                _to_bcd(month),
                _to_bcd(year % 100),
            ),
        )
        # The time is good again, so clear the flag that says it is not.
        status = self._read(_STATUS)[0]
        self._write(_STATUS, (status & ~_OSF & 0xFF,))

    @property
    def temperature(self):
        """The chip's own temperature in Celsius, to a quarter of a degree.

        It is there to compensate the crystal, and reads a little above room temperature
        because it is measuring its own package.
        """
        data = self._read(_TEMPERATURE, 2)
        whole = data[0] - 256 if data[0] > 127 else data[0]
        return whole + (data[1] >> 6) * 0.25

    @property
    def aging_offset(self):
        """Trims the crystal, roughly 0.1 parts per million per step, -128 to 127.

        A clock that gains a second a week is about 1.6ppm fast; a positive offset slows it
        down. The chip applies it on the next temperature conversion, not immediately.
        """
        value = self._read(_AGING_OFFSET)[0]
        return value - 256 if value > 127 else value

    @aging_offset.setter
    def aging_offset(self, value):
        self._write(_AGING_OFFSET, (value & 0xFF,))

    def sync_board(self):
        """Copies the module's time into the board's own clock, so time.localtime() is right.

        Boards forget the time when they lose power; this is the point of the module.
        """
        from machine import RTC

        year, month, day, hour, minute, second, weekday = self.datetime
        # machine.RTC wants the weekday in the middle and a subsecond on the end, unlike
        # everything else in MicroPython.
        RTC().datetime((year, month, day, weekday, hour, minute, second, 0))
        return self.datetime
