# Run with: python3 -B drivers/axs15231b/test_axs15231b.py
import importlib.util
import pathlib
import sys
import types

clock = [0]
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value, viper=lambda function: function)
sys.modules["time"] = types.SimpleNamespace(sleep_ms=lambda ms: clock.__setitem__(0, clock[0] + ms))
sys.modules["framebuf"] = types.SimpleNamespace(FrameBuffer=None, RGB565=1, MONO_HLSB=3)


class _Bus:
    """Decodes what the Viper code clocks out, the way the AXS15231B would read it."""

    def __init__(self):
        self.value = 0
        self.transfers = []
        self.samples = None

    def __getitem__(self, index):
        return self.value

    def __setitem__(self, index, value):
        rising = value & 0x20000 and not self.value & 0x20000
        self.value = value
        if rising and self.samples is not None:
            self.samples.append(tuple(value >> bit & 1 for bit in (13, 18, 21, 14)))  # D0..D3

    def begin(self):
        self.samples = []

    def end(self):
        samples, self.samples = self.samples, None
        header = 0
        for d0, _, d2, d3 in samples[:32]:
            header = header << 1 | d0
            assert d2 == 1 and d3 == 1, "D2 and D3 must stay high outside the quad data phase"
        rest = samples[32:]
        if header >> 24 == 0x32:
            nibbles = [d3 << 3 | d2 << 2 | d1 << 1 | d0 for d0, d1, d2, d3 in rest]
            data = bytes(nibbles[i] << 4 | nibbles[i + 1] for i in range(0, len(nibbles), 2))
        else:
            bits = [sample[0] for sample in rest]
            data = bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))
        self.transfers.append((header, data))


bus = _Bus()


class _Pin:
    OUT = 1
    levels = {}

    def __init__(self, number, mode=None, value=None):
        self.number = number
        if value is not None:
            self(value)

    def __call__(self, value=None):
        if value is None:
            return self.levels.get(self.number, 0)
        self.levels[self.number] = value
        if self.number == 12:  # CS
            bus.begin() if value == 0 else bus.end() if bus.samples is not None else None


sys.modules["machine"] = types.SimpleNamespace(Pin=_Pin)
here = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(here.parents[1] / "rgb565-display"))
spec = importlib.util.spec_from_file_location("axs15231b", here.with_name("axs15231b.py"))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
driver.ptr8 = lambda buffer: buffer
driver.ptr32 = lambda target: bus if isinstance(target, int) else target  # a register, or an array
driver.uname = lambda: types.SimpleNamespace(machine="Generic ESP32S3 module with ESP32-S3")


def command(code, data=b""):
    return (0x02000000 | code << 8, data)


# Setup wakes the panel, turns the image and backlight on, and leaves the touch/LCD reset released.
display = driver.AXS15231B()
assert bus.transfers == [command(driver.SLPOUT), command(driver.DISPON)]
assert _Pin.levels[1] == 1 and _Pin.levels[16] == 1
assert (display.width, display.height) == (180, 640)

# A rectangle selects its window, then sends every pixel high byte first on four lines.
bus.transfers.clear()
display.fill_rect(10, 20, 3, 2, driver.RED)
assert bus.transfers == [
    command(driver.CASET, b"\x00\x0a\x00\x0c"),
    command(driver.RASET, b"\x00\x14\x00\x15"),
    (0x32002C00, b"\xf8\x00" * 6),
]
assert bus.value & 0x204000 == 0x204000  # D2 and D3 back to idle high

# Buffers go out byte for byte, so every nibble value reaches the right data line.
bus.transfers.clear()
display.blit_buffer(b"\x12\x34\x56\x78\x9a\xbc\xde\xf0", 0, 636, 2, 2)
assert bus.transfers[-1] == (0x32002C00, b"\x12\x34\x56\x78\x9a\xbc\xde\xf0")
assert bus.transfers[1] == command(driver.RASET, b"\x02\x7c\x02\x7d")


def panel(transfers):
    """What the panel shows after these transfers, {(column, row): pixel}, as the real one draws it.

    It also fails on the window shapes the real panel garbles: one column wide and several rows
    tall, or wider and starting on a column where column % 4 == 3.
    """
    image = {}
    for header, data in transfers:
        if header == command(driver.CASET)[0]:
            left, right = data[0] << 8 | data[1], data[2] << 8 | data[3]
        elif header == command(driver.RASET)[0]:
            top, bottom = data[0] << 8 | data[1], data[2] << 8 | data[3]
        elif header == 0x32002C00:
            width, height = right - left + 1, bottom - top + 1
            assert len(data) == 2 * width * height
            if width * height > 1:
                assert not (width == 1 or left % 4 == 3), ("garbled window", left, top, right, bottom)
            for i in range(width * height):
                image[(left + i % width, top + i // width)] = data[2 * i:2 * i + 2]
    return image


def expected(rotation, x, y, w, h, pixels):
    return {driver._to_panel(rotation, x + dx, y + dy): pixels[2 * (dy * w + dx):2 * (dy * w + dx) + 2]
            for dy in range(h) for dx in range(w)}


# Every buffer pixel lands where _to_panel maps it, in each rotation and on awkward columns.
picture = bytes(range(24))  # 4 wide, 3 high, all pixels different
for rotation in (0, 1, 2, 3):
    display.rotation(rotation)
    for x, y in ((5, 7), (43, 9), (7, 40), (6, 5)):
        bus.transfers.clear()
        display.blit_buffer(picture, x, y, 4, 3)
        assert panel(bus.transfers) == expected(rotation, x, y, 4, 3, picture), (rotation, x, y)
        bus.transfers.clear()
        display.fill_rect(x, y, 5, 2, driver.RED)
        assert panel(bus.transfers) == expected(rotation, x, y, 5, 2, b"\xf8\x00" * 10), (rotation, x, y)
        bus.transfers.clear()
        display.hline(x, y, 6, driver.BLUE)
        display.vline(x, y + 3, 6, driver.GREEN)
        painted = panel(bus.transfers)
        assert painted == {**expected(rotation, x, y, 6, 1, b"\x00\x1f" * 6), **expected(rotation, x, y + 3, 1, 6, b"\x07\xe0" * 6)}
display.rotation(1)
assert (display.width, display.height) == (640, 180)
display.rotation(0)


class _I2C:
    def __init__(self):
        self.frame = bytes(8)

    def writeto(self, address, data):
        assert address == 0x3B and data == driver._READ_TOUCH

    def readfrom_into(self, address, buffer):
        if self.frame is None:
            raise OSError(19)
        buffer[:] = self.frame


counter = 0x10


def report(along, across, event=2):
    """A new touch report as the controller sends it: event 2 is contact, 1 is lift."""
    global counter
    counter = (counter + 2) & 0xFF
    return bytes((0, 1, event << 6 | along >> 8, along & 255, across >> 8, across & 255, counter, (counter + 1) & 0xFF))


i2c = _I2C()
touch = driver.AXS15231BTouch(i2c)
assert touch.read() is None  # an empty frame: nothing touches

# The calibration edges land on the screen edges (USB at the bottom), and beyond them it clamps.
left, right, top, bottom = touch.calibration
for raw, edge in (((top, left), (0, 0)), ((bottom, right), (179, 639)), ((639, 0), (0, 0)), ((0, 179), (179, 639))):
    i2c.frame = report(*raw)
    assert touch.read() == edge, raw

# A resting finger sends no new reports: garbled frames, repeats and I2C errors keep it down.
i2c.frame = report(320, 80)
point = touch.read()
repeat = i2c.frame
for frame in (bytes.fromhex("ffffffffff947e7e"), bytes.fromhex("7e7e7e7e7e7e7e7e"), bytes.fromhex("0001800001801700"), repeat, None):
    i2c.frame = frame
    assert touch.read() == point, frame
i2c.frame = report(300, 90)
assert touch.read() not in (None, point)

# A lift report releases it, and garbled frames afterwards do not bring it back.
i2c.frame = report(300, 90, event=1)
assert touch.read() is None
i2c.frame = bytes.fromhex("7e7e7e7e7e7e7e7e")
assert touch.read() is None

# With the display's rotation, a touch lands on the same pixel _to_panel draws.
i2c.frame = report(320, 80)
portrait = touch.read()
for rotation in (1, 2, 3):
    touch.rotation = rotation
    i2c.frame = report(320, 80)
    x, y = touch.read()
    assert driver._to_panel(rotation, x, y) == portrait, rotation

print("axs15231b: ok")
