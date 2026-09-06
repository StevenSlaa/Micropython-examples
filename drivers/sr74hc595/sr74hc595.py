# Driver for the 74HC595 8 bit serial in, parallel out shift register.
# The module is called sr74hc595 because a Python module name cannot start with a digit.
#
# Three pins drive any number of chained registers: data (DS/SER), clock (SHCP/SRCLK) and
# latch (STCP/RCLK). Outputs do not change until the latch pulses, so a whole chain updates
# at once rather than rippling visibly.

_ALL_BITS = 0xFF


class ShiftRegister:
    """One or more chained 74HC595s.

    `count` is how many are daisy chained, giving `count * 8` outputs numbered from the first
    register's QA. `msb_first` matches how nearly everything is wired; flip it if your outputs
    come out back to front.
    """

    def __init__(self, data, clock, latch, count=1, msb_first=True):
        self.data = data
        self.clock = clock
        self.latch = latch
        for pin in (data, clock, latch):
            pin.init(pin.OUT, value=0)
        self.count = count
        self.msb_first = msb_first
        self.values = bytearray(count)
        self.write()

    def _shift(self, value):
        # ponytail: bit banged, so a few kHz rather than a few MHz. Fast enough for a display
        # being read by a person; drive DS and SHCP from SPI if you need to push frames.
        for bit in range(7, -1, -1) if self.msb_first else range(8):
            self.data((value >> bit) & 1)
            self.clock(1)
            self.clock(0)

    def write(self, values=None):
        """Sends the current bytes and latches them, one byte per register in the chain."""
        if values is not None:
            values = (values,) if isinstance(values, int) else values
            if len(values) != self.count:
                raise ValueError("Expected %d byte(s), one per register" % self.count)
            self.values = bytearray(byte & _ALL_BITS for byte in values)
        # The first byte shifted out travels furthest along the chain, so the last register's
        # byte has to go first.
        for value in reversed(self.values):
            self._shift(value)
        self.latch(1)
        self.latch(0)

    def __getitem__(self, register):
        return self.values[register]

    def __setitem__(self, register, value):
        self.values[register] = value & _ALL_BITS
        self.write()

    def pin(self, output, on=True):
        """Turns one output on or off, numbered from QA of the first register."""
        register, bit = divmod(output, 8)
        if on:
            self.values[register] |= 1 << bit
        else:
            self.values[register] &= ~(1 << bit) & _ALL_BITS
        self.write()

    def clear(self):
        """Turns every output off."""
        self.write(bytearray(self.count))
