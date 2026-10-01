# Driver for the Avia Semiconductor HX711, the 24 bit ADC on load cell amplifier boards.
# Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
#
# The HX711 is not I2C or SPI. It pulls DOUT low when a reading is ready, then shifts it out one
# bit per clock pulse on PD_SCK, most significant bit first, in two's complement. One to three
# extra pulses after the 24 data bits choose the channel and gain of the *next* reading. Holding
# PD_SCK high for more than 60us powers the chip down.

from machine import Pin, disable_irq, enable_irq
from time import sleep_us, ticks_diff, ticks_ms

# Gain, and so the channel, to the number of extra clock pulses that selects it.
_PULSES = {128: 1, 32: 2, 64: 3}  # 128 and 64 are channel A, 32 is channel B


class HX711:
    """An HX711 with its DOUT and PD_SCK on the pins `dout` and `pd_sck`.

    `gain` is 128 or 64 for channel A, where the load cell usually is, or 32 for channel B.
    `offset` is the raw reading with the scale empty and `scale` the raw counts per unit of
    weight: `tare()` and `calibrate()` measure them, and passing them back in skips both on the
    next boot. `timeout_ms` is how long to wait for a reading before giving up.
    """

    def __init__(self, dout, pd_sck, gain=128, offset=0, scale=1.0, timeout_ms=1000):
        self._dout = Pin(dout, Pin.IN)
        self._sck = Pin(pd_sck, Pin.OUT)
        self._sck.value(0)
        self.offset = offset
        self.scale = scale
        self.timeout_ms = timeout_ms
        self.gain = gain

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, gain):
        if gain not in _PULSES:
            raise ValueError("gain must be 128 or 64 (channel A) or 32 (channel B)")
        self._gain = gain
        self._pulses = _PULSES[gain]
        # The pulses after this reading set the new gain; the reading itself used the old one.
        self.read_raw()

    def is_ready(self):
        """True when a reading is waiting, so `read_raw()` returns without blocking."""
        return self._dout.value() == 0

    def read_raw(self):
        """One signed 24 bit reading, straight from the chip."""
        start = ticks_ms()
        while self._dout.value():
            if ticks_diff(ticks_ms(), start) > self.timeout_ms:
                raise OSError("No HX711 reading: check DOUT, PD_SCK and power")
        sck, dout = self._sck.value, self._dout.value
        value = 0
        # An interrupt that holds the clock high past 60us would power the chip down mid-read.
        state = disable_irq()
        try:
            for _ in range(24):
                sck(1)
                sck(0)
                value = (value << 1) | dout()
            for _ in range(self._pulses):
                sck(1)
                sck(0)
        finally:
            enable_irq(state)
        return value - 0x1000000 if value & 0x800000 else value

    def read(self, samples=5):
        """The average of the middle half of `samples` raw readings, so a stray bad reading is
        dropped instead of dragging the average."""
        values = sorted(self.read_raw() for _ in range(samples))
        quarter = samples // 4
        middle = values[quarter : samples - quarter]
        return sum(middle) / len(middle)

    def weight(self, samples=5):
        """The weight on the scale, in whatever unit `calibrate()` was given."""
        return (self.read(samples) - self.offset) / self.scale

    def tare(self, samples=15):
        """Take the current load as zero. Run it with the scale empty."""
        self.offset = self.read(samples)
        return self.offset

    def calibrate(self, known_weight, samples=15):
        """Set the scale from `known_weight` sitting on a tared scale, and return it."""
        if known_weight <= 0:
            raise ValueError("known_weight must be above zero")
        # ponytail: a single point is enough for a load cell, which is linear across its range.
        self.scale = (self.read(samples) - self.offset) / known_weight
        return self.scale

    def power_down(self):
        """Put the chip to sleep, drawing under 1uA, until `power_up()`."""
        self._sck.value(0)
        self._sck.value(1)
        sleep_us(80)

    def power_up(self):
        """Wake the chip. It comes back on channel A at gain 128, so the gain is set again."""
        self._sck.value(0)
        self.gain = self._gain
