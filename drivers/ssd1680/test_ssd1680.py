# Run with: python3 -B drivers/ssd1680/test_ssd1680.py
# A stand-in framebuf with MicroPython's byte layouts, and a fake SPI bus that records commands, so
# the colour bits, the rotations and the refresh sequence can be checked off-board.
import sys, types

MONO_VLSB, MONO_HLSB = 0, 3


class _FrameBuffer:
    def __init__(self, buffer, width, height, mode):
        self.buffer, self.width, self.height, self.mode = buffer, width, height, mode

    def _locate(self, x, y):
        if self.mode == MONO_HLSB:
            return y * ((self.width + 7) // 8) + x // 8, 7 - x % 8
        return (y // 8) * self.width + x, y % 8  # MONO_VLSB: least significant bit on top

    def pixel(self, x, y, c=None):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        index, bit = self._locate(x, y)
        if c is None:
            return (self.buffer[index] >> bit) & 1
        if c:
            self.buffer[index] |= 1 << bit
        else:
            self.buffer[index] &= ~(1 << bit) & 0xFF

    def fill(self, c):
        for index in range(len(self.buffer)):
            self.buffer[index] = 0xFF if c else 0

    def fill_rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.pixel(xx, yy, c)

    def text(self, s, x, y, c=1):
        # A stand-in font: every character is its top left and bottom right pixel.
        for i in range(len(s)):
            self.pixel(x + 8 * i, y, c)
            self.pixel(x + 8 * i + 7, y + 7, c)


clock = [0]


def _sleep_ms(ms):
    clock[0] += ms


sys.modules["framebuf"] = types.SimpleNamespace(FrameBuffer=_FrameBuffer, MONO_VLSB=MONO_VLSB, MONO_HLSB=MONO_HLSB)
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["time"] = types.SimpleNamespace(
    sleep_ms=_sleep_ms, ticks_ms=lambda: clock[0], ticks_diff=lambda end, start: end - start
)
from ssd1680 import BLACK, RED, SSD1680, WHITE  # noqa: E402


class _Pin:
    OUT, IN = 1, 0

    def __init__(self, high_reads=0):
        self.level = 0
        self.levels = []
        self.high_reads = high_reads  # for BUSY: how many reads say busy

    def init(self, mode, value=None):
        if value is not None:
            self.level = value

    def value(self, level=None):
        if level is None:
            if self.high_reads:
                self.high_reads -= 1
                return 1
            return self.level
        self.level = level
        self.levels.append(level)


class _SPI:
    def __init__(self, cs, dc):
        self.cs, self.dc, self.frames = cs, dc, []

    def write(self, data):
        assert self.cs.level == 0, "written with CS low"
        self.frames.append((self.dc.level, bytes(data)))

    def commands(self):
        commands = []
        for dc, data in self.frames:
            if dc:
                commands[-1][1].extend(data)
            else:
                commands.extend([byte, bytearray()] for byte in data)
        return [(command, bytes(data)) for command, data in commands]


def display(rotation=90, busy_reads=0, **kwargs):
    cs, dc, rst, busy = _Pin(), _Pin(), _Pin(), _Pin(high_reads=busy_reads)
    return SSD1680(_SPI(cs, dc), cs, dc, rst, busy, rotation=rotation, **kwargs)


# Colours are a bit in each image: black 1 is white, red 1 is red.
screen = display(rotation=0)
for color, black, red in ((WHITE, 0xFF, 0x00), (BLACK, 0x00, 0x00), (RED, 0xFF, 0xFF)):
    screen.fill(color)
    assert set(screen._black_buffer) == {black} and set(screen._red_buffer) == {red}, color

# Rotations: every drawn pixel lands where the rotation says, checked against a pixel by pixel map.
seed = [12345]


def rand(n):
    seed[0] = (seed[0] * 1103515245 + 12345) % 2**31
    return seed[0] % n


def expected(points, rotation):
    out = bytearray(4736)
    for x, y in points:
        panel_x, panel_y = {0: (x, y), 90: (127 - y, x), 180: (127 - x, 295 - y), 270: (y, 295 - x)}[rotation]
        out[panel_y * 16 + panel_x // 8] |= 0x80 >> (panel_x % 8)
    return bytes(out)


for rotation in (0, 90, 180, 270):
    screen = display(rotation)
    w, h = screen.width, screen.height
    assert (w, h) == ((296, 128) if rotation in (90, 270) else (128, 296)), (rotation, w, h)
    points = {(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (1, 2), (w // 2, h // 3)}
    points.update((rand(w), rand(h)) for _ in range(400))
    for x, y in points:
        screen.pixel(x, y, RED)
    assert bytes(screen._native(screen._red_buffer)) == expected(points, rotation), rotation
    assert set(screen._native(screen._black_buffer)) == {0xFF}, "red leaves the black image white"

# The refresh: reset, the SSD1680 set-up, both images, a full refresh, deep sleep.
screen = display(rotation=0, busy_reads=5)
screen.pixel(0, 0, BLACK)
screen.pixel(127, 295, RED)
screen.show()
assert screen.rst.levels[:2] == [0, 1], "a hardware reset first"
commands = screen.spi.commands()
assert [c for c, _ in commands] == [
    0x12, 0x01, 0x11, 0x3C, 0x18, 0x21, 0x44, 0x45, 0x4E, 0x4F, 0x24, 0x26, 0x22, 0x20, 0x10
], [hex(c) for c, _ in commands]
data = dict(commands)
assert data[0x01] == b"\x27\x01\x00" and data[0x11] == b"\x03"
assert data[0x44] == b"\x00\x0f" and data[0x45] == b"\x00\x00\x27\x01"
assert data[0x22] == b"\xf7" and data[0x20] == b"" and data[0x10] == b"\x01"
black, red = data[0x24], data[0x26]
assert len(black) == len(red) == 4736
assert black[0] == 0x7F and set(black[1:]) == {0xFF}, "top left pixel black"
assert red[-1] == 0x01 and set(red[:-1]) == {0x00}, "bottom right pixel red"
assert screen.cs.level == 1

# A panel that never stops being busy is reported, instead of hanging the board.
stuck = display(busy_reads=10**9, busy_timeout_ms=100)
try:
    stuck.show()
    raise AssertionError("a stuck BUSY must be reported")
except OSError as error:
    assert "BUSY" in str(error), error

# Scaled text: each font pixel becomes a scale by scale block.
screen = display(rotation=0)
screen.text("A", 10, 20, BLACK, scale=3)
black_pixels = {(x, y) for x in range(128) for y in range(296) if screen._black.pixel(x, y) == 0}
assert black_pixels == {(x, y) for x in range(10, 13) for y in range(20, 23)} | {
    (x, y) for x in range(31, 34) for y in range(41, 44)
}, sorted(black_pixels)

# A bitmap: 1 bits in the colour, 0 bits leave what was there. Two rows of 10 pixels: the first
# row has its first and last pixel set, the second row is full.
screen = display(rotation=0)
screen.fill(RED)
screen.bitmap(bytes((0b10000000, 0b01000000, 0xFF, 0b11000000)), 5, 7, 10, 2, BLACK)
black_pixels = {(x, y) for x in range(128) for y in range(296) if screen._black.pixel(x, y) == 0}
assert black_pixels == {(5, 7), (14, 7)} | {(x, 8) for x in range(5, 15)}, sorted(black_pixels)
assert screen._red.pixel(5, 7) == 0, "a black pixel is not red"
assert screen._red.pixel(6, 7) == 1, "a 0 bit leaves the red that was there"

for bad in ({"rotation": 45},):
    try:
        display(**bad)
        raise AssertionError("refused: %r" % bad)
    except ValueError:
        pass
try:
    screen.fill(3)
    raise AssertionError("an unknown colour must be refused")
except ValueError:
    pass

print("ssd1680: ok")
