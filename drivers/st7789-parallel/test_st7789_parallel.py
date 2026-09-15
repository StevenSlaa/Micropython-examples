# Run with: python3 -B drivers/st7789-parallel/test_st7789_parallel.py
import importlib.util
import pathlib
import sys
import types


clock = [0]
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value, viper=lambda function: function)
sys.modules["time"] = types.SimpleNamespace(
    sleep_ms=lambda milliseconds: clock.__setitem__(0, clock[0] + milliseconds)
)


class _FrameBuffer:
    def __init__(self, buffer, width, height, mode):
        self.buffer, self.width, self.height = buffer, width, height

    def fill(self, color):
        # Like MicroPython on the ESP32, store RGB565 values little-endian.
        self.buffer[:] = color.to_bytes(2, "little") * (len(self.buffer) // 2)

    def text(self, string, x, y, color):
        # Enough of a fake font to verify the driver's byte swap: light the first and last pixel.
        self.buffer[:2] = self.buffer[-2:] = color.to_bytes(2, "little")

    def pixel(self, x, y, color):
        index = 2 * (y * self.width + x)
        self.buffer[index:index + 2] = color.to_bytes(2, "little")

    def blit(self, source, x, y, key, palette):
        # Only what bitmap() uses: a MONO_HLSB source mapped through a two-colour palette.
        row_bytes = (source.width + 7) // 8
        for row in range(source.height):
            for column in range(source.width):
                bit = 1 if source.buffer[row * row_bytes + column // 8] & (0x80 >> (column & 7)) else 0
                self.pixel(x + column, y + row, int.from_bytes(palette.buffer[2 * bit:2 * bit + 2], "little"))


_framebuf = types.SimpleNamespace(FrameBuffer=_FrameBuffer, RGB565=1, MONO_HLSB=3)
sys.modules["framebuf"] = _framebuf


class _Pin:
    OUT = 1
    pins = {}
    writes = []

    def __init__(self, name):
        self.name = name
        self.level = 0
        self.mode = None
        self.pins[name] = self

    def init(self, mode, value=None):
        self.mode = mode
        if value is not None:
            self.value(value)

    def value(self, value=None):
        if value is None:
            return self.level
        previous = self.level
        self.level = value
        if self.name == "wr" and previous == 0 and value == 1:
            pins = self.pins
            if "cs" in pins and pins["cs"].level == 0:
                byte = sum(pins["d%d" % bit].level << bit for bit in range(8))
                self.writes.append((pins["dc"].level, byte))


def _pins():
    _Pin.pins = {}
    _Pin.writes = []
    data = [_Pin("d%d" % bit) for bit in range(8)]
    wr, dc, cs = _Pin("wr"), _Pin("dc"), _Pin("cs")
    wr.level = dc.level = cs.level = 1
    return data, wr, dc, cs, _Pin("reset"), _Pin("rd"), _Pin("backlight")


# The drawing methods live in the shared rgb565-display driver.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rgb565-display"))
module_path = pathlib.Path(__file__).with_name("st7789_parallel.py")
spec = importlib.util.spec_from_file_location("st7789_parallel", module_path)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


# Viper's ptr8/ptr32 casts, backed by a fake register map that records every write.
register_values = {}
register_writes = []


class _Register:
    def __init__(self, address):
        self.address = address

    def __getitem__(self, index):
        return register_values.get(self.address, 0)

    def __setitem__(self, index, value):
        register_values[self.address] = value
        register_writes.append((self.address, value))


driver.ptr8 = lambda buffer: buffer
driver.ptr32 = _Register
OUT_SET, OUT_CLEAR, OUT1 = 0x60004008, 0x6000400C, 0x60004010
DC, WR = 0x80, 0x100


def _display(rotation=1, clear=True):
    data, wr, dc, cs, reset, rd, backlight = _pins()
    display = driver.ST7789Parallel(data, wr, dc, cs, reset, rd, backlight, rotation=rotation)
    if clear:
        _Pin.writes.clear()
    return display, (data, wr, dc, cs, reset, rd, backlight)


def _commands():
    commands = []
    for dc, byte in _Pin.writes:
        if dc == 0:
            commands.append([byte, bytearray()])
        else:
            assert commands, "data arrived before a command"
            commands[-1][1].append(byte)
    return [(command, bytes(data)) for command, data in commands]


# Initialization uses the panel sequence, rotates to landscape and enables the backlight.
display, pins = _display(1, clear=False)
assert (display.width, display.height, display.x_offset, display.y_offset) == (320, 170, 0, 35)
assert pins[-1].level == 1 and pins[-2].level == 1  # backlight and RD
assert clock[0] >= 525
commands = _commands()
assert [command for command, _ in commands[:4]] == [driver.SLPOUT, driver.NORON, driver.MADCTL, 0xB6]
assert commands[2] == (driver.MADCTL, b"\x08")
assert (driver.COLMOD, b"\x55") in commands
assert (0xE0, b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17") in commands
assert commands[-2:] == [
    (driver.DISPON, b""),
    (driver.MADCTL, b"\x68"),
]
_Pin.writes.clear()

# Every rotation has the right logical geometry and controller RAM offset.
expected_rotations = (
    (170, 320, 35, 0),
    (320, 170, 0, 35),
    (170, 320, 35, 0),
    (320, 170, 0, 35),
)
for rotation, expected in enumerate(expected_rotations):
    display.rotation(rotation)
    assert (display.width, display.height, display.x_offset, display.y_offset) == expected
    expected_madctl = (0x08, 0x68, 0xC8, 0xA8)[rotation]
    assert _commands()[-1] == (driver.MADCTL, bytes((expected_madctl,)))

# A landscape top-left pixel maps to controller row 35 and sends high-byte-first RGB565.
_Pin.writes.clear()
display.rotation(1)
_Pin.writes.clear()
display.pixel(0, 0, driver.RED)
assert _commands() == [
    (driver.CASET, b"\x00\x00\x00\x00"),
    (driver.RASET, b"\x00\x23\x00\x23"),
    (driver.RAMWR, b"\xf8\x00"),
]

# Rectangles clip to the visible area and emit the clipped number of pixels.
_Pin.writes.clear()
display.fill_rect(-1, -1, 3, 3, driver.BLUE)
commands = _commands()
assert commands[:2] == [(driver.CASET, b"\x00\x00\x00\x01"), (driver.RASET, b"\x00\x23\x00\x24")]
assert commands[2] == (driver.RAMWR, b"\x00\x1f" * 4)

# Straight lines become one rectangle, whichever end comes first.
_Pin.writes.clear()
display.line(5, 2, 2, 2, driver.RED)
assert _commands() == [
    (driver.CASET, b"\x00\x02\x00\x05"),
    (driver.RASET, b"\x00\x25\x00\x25"),
    (driver.RAMWR, b"\xf8\x00" * 4),
]

# Text swaps colour bytes for framebuf's little-endian RGB565 so the panel gets big-endian data.
_Pin.writes.clear()
display.text("A", 8, 10, driver.RED, driver.NAVY)
data = _commands()[-1][1]
assert len(data) == 8 * 8 * 2
assert data[:2] == b"\xf8\x00" and data[-2:] == b"\xf8\x00"
assert data[2:-2] == b"\x00\x0f" * 62

# Bitmaps draw 1 bits in the colour and 0 bits in the background, high byte first.
_Pin.writes.clear()
display.bitmap(b"\x80\x01", 4, 5, 8, 2, driver.RED, driver.NAVY)
commands = _commands()
assert commands[:2] == [(driver.CASET, b"\x00\x04\x00\x0b"), (driver.RASET, b"\x00\x28\x00\x29")]
assert commands[2] == (driver.RAMWR, b"\xf8\x00" + b"\x00\x0f" * 14 + b"\xf8\x00")

# Invalid setup and invalid buffers fail early and clearly.
data, wr, dc, cs, reset, rd, backlight = _pins()
try:
    driver.ST7789Parallel(data[:7], wr, dc, cs)
    raise AssertionError("seven data pins must be rejected")
except ValueError:
    pass

try:
    display.blit_buffer(b"\x00", 0, 0, 1, 1)
    raise AssertionError("a short RGB565 buffer must be rejected")
except ValueError:
    pass

# The fast bus drives DC, maps D0 to GPIO39 and D7 to GPIO48 in one OUT1 write, then pulses WR.
register_values[OUT1] = 0x40 | (1 << 8)  # GPIO38 (backlight) and a stale data bit
register_writes.clear()
driver._bus_viper(0x01, b"\x80", 1)
assert register_writes == [
    (OUT_CLEAR, DC),
    (OUT1, 0x40 | (1 << 7)),
    (OUT_CLEAR, WR),
    (OUT_SET, WR),
    (OUT_SET, DC),
    (OUT1, 0x40 | (1 << 16)),
    (OUT_CLEAR, WR),
    (OUT_SET, WR),
]

register_writes.clear()
driver._fill_viper(driver.RED, 1)
assert register_writes == [
    (OUT1, 0x40 | (1 << 10) | (0xF << 13)),  # 0xF8: D3 and D4..D7
    (OUT_CLEAR, WR),
    (OUT_SET, WR),
    (OUT1, 0x40),  # 0x00
    (OUT_CLEAR, WR),
    (OUT_SET, WR),
]

# Symmetric colours set the data bus once and only pulse WR for all bytes.
register_values[OUT1] = 0x40
register_writes.clear()
driver._fill_viper(driver.WHITE, 2)
assert register_writes == [(OUT1, 0x40 | 0x1E780)] + [(OUT_CLEAR, WR), (OUT_SET, WR)] * 4

print("st7789_parallel: ok")
