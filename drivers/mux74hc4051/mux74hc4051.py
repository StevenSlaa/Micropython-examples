# Driver for the 74HC4051 eight channel analog multiplexer, and its twins the CD74HC4051 and the
# 74HCT4051.
#
# The chip is a rotary switch made of transistors: three select pins pick which of the eight
# channels, Y0 to Y7, is connected to the common pin Z. The connection works both ways, so it can
# spread one analog input over eight sensors, or send one signal out to eight places.

from time import sleep_ms


class Mux74HC4051:
    """A 74HC4051 with its select pins S0, S1 and S2 on the Pin objects `s0`, `s1` and `s2`.

    `enable` is the optional Pin on E, which is active low; without it, tie E to GND. `adc` is an
    optional ADC on the common pin Z, which read() uses. `settle_ms` is how long to wait after
    switching before reading, so the ADC sees the new channel and not a trace of the old one.
    """

    def __init__(self, s0, s1, s2, enable=None, adc=None, settle_ms=1):
        self._select = (s0, s1, s2)
        for pin in self._select:
            pin.init(pin.OUT, value=0)
        self._enable = enable
        self._enabled = True
        if enable is not None:
            enable.init(enable.OUT, value=0)  # low is on
        self.adc = adc
        self.settle_ms = settle_ms
        self._channel = 0

    @property
    def channel(self):
        """The channel connected to Z, 0 to 7."""
        return self._channel

    @channel.setter
    def channel(self, channel):
        if not isinstance(channel, int) or not 0 <= channel <= 7:
            raise ValueError("channel must be 0 to 7")
        # The three select pins cannot change at the same instant, so on the way from one channel
        # to another the chip briefly connects whichever channels lie in between. With an enable
        # pin it is switched off for the change: break before make.
        pause = self._enable is not None and self._enabled
        if pause:
            self._enable.value(1)
        for bit, pin in enumerate(self._select):
            pin.value((channel >> bit) & 1)
        if pause:
            self._enable.value(0)
        self._channel = channel

    @property
    def enabled(self):
        """False disconnects every channel from Z. Needs the enable pin."""
        return self._enabled

    @enabled.setter
    def enabled(self, on):
        if self._enable is None:
            raise ValueError("Pass enable= to switch the multiplexer on and off")
        self._enable.value(0 if on else 1)
        self._enabled = bool(on)

    def read(self, channel):
        """Selects `channel` and returns the ADC reading on it, 0 to 65535."""
        if self.adc is None:
            raise ValueError("Pass adc= to read through the multiplexer")
        if channel != self._channel:
            self.channel = channel
            sleep_ms(self.settle_ms)
        return self.adc.read_u16()

    def read_all(self):
        """The readings on all eight channels, Y0 first."""
        return [self.read(channel) for channel in range(8)]
