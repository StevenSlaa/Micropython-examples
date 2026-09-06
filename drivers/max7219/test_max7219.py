# Run with: python3 -B drivers/max7219/test_max7219.py
# Stubs framebuf and SPI so the chain ordering and the transpose can be checked off-board.
import sys, types


class _FrameBuffer:
    """Only what the driver uses of framebuf: a MONO_HLSB buffer and the primitives it forwards."""

    MONO_HLSB = 0

    def __init__(self, buffer, width, height, layout):
        self.buffer, self.width, self.height = buffer, width, height

    def fill(self, colour):
        for index in range(len(self.buffer)):
            self.buffer[index] = 0xFF if colour else 0x00

    def pixel(self, x, y, colour=1):
        index = y * (self.width // 8) + (x // 8)
        if colour:
            self.buffer[index] |= 1 << (7 - (x % 8))
        else:
            self.buffer[index] &= ~(1 << (7 - (x % 8))) & 0xFF

    def _unused(self, *args, **kwargs):
        pass

    hline = vline = line = rect = fill_rect = text = scroll = blit = _unused


sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["framebuf"] = types.SimpleNamespace(
    FrameBuffer=_FrameBuffer, MONO_HLSB=_FrameBuffer.MONO_HLSB
)
from max7219 import Matrix8x8  # noqa: E402


class _Pin:
    def __init__(self):
        self.OUT = 3
        self.levels = []

    def init(self, mode, value):
        pass

    def __call__(self, level):
        self.levels.append(level)


class _SPI:
    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(bytes(data))


def matrix(**kwargs):
    spi, cs = _SPI(), _Pin()
    display = Matrix8x8(spi, cs, 4, **kwargs)
    spi.written.clear()  # drop the init sequence
    return display, spi


# Brightness is a chain-wide command: one write per module, and out of range is refused.
display, spi = matrix()
display.brightness(7)
assert spi.written == [bytes([10, 7])] * 4, spi.written
for bad in (-1, 16):
    try:
        display.brightness(bad)
        raise AssertionError("brightness %d must be refused" % bad)
    except ValueError:
        pass

# One lit pixel in the top left corner is one bit in the first module's first row.
display, spi = matrix()
display.pixel(0, 0, 1)
display.show()
assert len(spi.written) == 8 * 4, "one write per row per module"
assert spi.written[0] == bytes([1, 0x80]), spi.written[0]
assert spi.written[1] == bytes([1, 0x00]), "the other modules stay dark"

# reverse=True sends the modules the other way round, for a board chained from the far end.
display, spi = matrix(reverse=True)
display.pixel(0, 0, 1)
display.show()
assert spi.written[3] == bytes([1, 0x80]), "the lit module is now written last"
assert spi.written[0] == bytes([1, 0x00])

# transpose=True turns each 8x8 block a quarter turn: a pixel on the top row of a module moves
# to that module's first column.
display, spi = matrix(transpose=True)
display.pixel(1, 0, 1)  # second column of the top row
display.show()
assert spi.written[0] == bytes([1, 0x00]), "no longer on the top row"
assert spi.written[4] == bytes([2, 0x80]), "it is on the second row, first column now"

# Swapping rows and columns twice is the identity, whatever the pattern.
display, _ = matrix(transpose=True)
for x, y in ((0, 0), (3, 6), (9, 1), (31, 7)):
    display.pixel(x, y, 1)
original = bytes(display.buffer)
display.buffer[:] = display._transposed()
assert bytes(display.buffer) != original, "the swap changed something"
display.buffer[:] = display._transposed()
assert bytes(display.buffer) == original, "and swapping back restores it"

print("max7219: ok")
