# Driver for the P9813 constant current RGB LED driver, as used by chainable RGB LED modules
# and some RGB strips. Not to be confused with the WS2812B family: this one has a clock line.
#
# A frame is 32 zero bits, then four bytes per LED, then 32 more zero bits. The first of those
# four is a checksum byte carrying the inverted top two bits of each colour, which is what the
# chip uses to tell a real frame from noise on the wire.


def checksum(red, green, blue):
    """The byte that precedes each colour: 1, 1, then the inverted top two bits of B, G and R."""
    return (
        0xC0
        | (((~blue & 0xFF) >> 6) << 4)
        | (((~green & 0xFF) >> 6) << 2)
        | ((~red & 0xFF) >> 6)
    )


class P9813:
    """A chain of `n` P9813 driven LEDs on a clock and a data pin.

    Colours are (red, green, blue), 0 to 255 each. Nothing changes on the LEDs until write().
    """

    def __init__(self, clock, data, n=1, brightness=1.0):
        self.clock = clock
        self.data = data
        for pin in (clock, data):
            pin.init(pin.OUT, value=0)
        self.n = n
        self.buf = bytearray(3 * n)
        self.brightness = brightness
        self.write()

    def _byte(self, value):
        # ponytail: bit banged, a few kHz. Fine for a handful of LEDs being watched by a
        # person; drive the clock and data lines from SPI if you need a frame rate.
        for bit in range(7, -1, -1):
            self.data((value >> bit) & 1)
            self.clock(0)
            self.clock(1)

    def _frame(self):
        """The 32 zero bits that start and end every frame."""
        for _ in range(4):
            self._byte(0x00)

    def __len__(self):
        return self.n

    def __setitem__(self, index, colour):
        offset = (index % self.n) * 3
        self.buf[offset], self.buf[offset + 1], self.buf[offset + 2] = colour

    def __getitem__(self, index):
        offset = (index % self.n) * 3
        return tuple(self.buf[offset : offset + 3])

    def fill(self, colour):
        for index in range(self.n):
            self[index] = colour

    def write(self):
        """Sends the whole chain. Brightness is applied here, so changing it takes effect now."""
        scale = min(max(self.brightness, 0.0), 1.0)
        self._frame()
        for index in range(self.n):
            red, green, blue = (int(value * scale) for value in self[index])
            self._byte(checksum(red, green, blue))
            # The chip wants blue first and red last, which is not the order anyone stores them.
            self._byte(blue)
            self._byte(green)
            self._byte(red)
        self._frame()
