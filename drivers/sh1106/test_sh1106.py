# Run with: python3 -B drivers/sh1106/test_sh1106.py
# The change made to this driver is the column offset, so that is what is checked: the exact
# commands sent before each page, which is what decides where the pixels land on the glass.
import sys, types


class _FrameBuffer:
    MONO_VLSB = 0
    MONO_HMSB = 1

    def __init__(self, buffer, width, height, layout):
        self.buffer, self.width, self.height = buffer, width, height

    def fill(self, colour):
        for index in range(len(self.buffer)):
            self.buffer[index] = 0xFF if colour else 0

    def _nothing(self, *args, **kwargs):
        pass

    pixel = text = line = hline = vline = blit = scroll = fill_rect = rect = ellipse = _nothing


sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["framebuf"] = types.SimpleNamespace(
    FrameBuffer=_FrameBuffer, MONO_VLSB=0, MONO_HMSB=1
)
sys.modules["utime"] = types.SimpleNamespace(sleep_ms=lambda ms: None)
from sh1106 import PANEL_72X40, SH1106_I2C  # noqa: E402


class _I2C:
    def __init__(self):
        self.commands = []
        self.data = []

    def writeto(self, address, buffer):
        assert address == 0x3C
        if buffer[0] == 0x80:
            self.commands.append(buffer[1])
        else:
            assert buffer[0] == 0x40, "data is prefixed with 0x40"
            self.data.append(bytes(buffer[1:]))


def display(width, height, **kwargs):
    bus = _I2C()
    panel = SH1106_I2C(width, height, bus, **kwargs)
    panel.startup = list(bus.commands)  # what was sent before the first frame
    bus.commands.clear()
    bus.data.clear()
    return panel, bus


def column_commands(commands):
    """The page, low column and high column commands, in the order they were sent."""
    return [(c & 0xF0, c & 0x0F) for c in commands if c >= 0xB0 or 0x00 <= c <= 0x1F]


# The usual 128 wide panel keeps the offset it always had: 2 into the 132 columns.
panel, bus = display(128, 64)
assert panel.x_offset == 2
panel.fill(0)
panel.show(full_update=True)
assert (0x00, 0x02) in column_commands(bus.commands), bus.commands
assert (0x10, 0x00) in column_commands(bus.commands), "high nibble zero for an offset under 16"

# The 72x40 panel on an ESP32-C3 SuperMini sits at column 30, which needs both nibbles.
panel, bus = display(72, 40)
assert panel.x_offset == 30, panel.x_offset
panel.fill(0)
panel.show(full_update=True)
assert (0x00, 0x0E) in column_commands(bus.commands), "30 & 0x0f is 14"
assert (0x10, 0x01) in column_commands(bus.commands), "30 >> 4 is 1, which the old fixed 2 never sent"

# Every page is written separately, which is the whole difference from an SSD1306: a page
# addressed controller wraps within its own page rather than running on to the next.
assert len(bus.data) == 5, "five pages for a 40 pixel tall panel"
assert all(len(chunk) == 72 for chunk in bus.data), "and one row of the panel's width each"
pages = [c for c in bus.commands if 0xB0 <= c <= 0xB7]
assert pages == [0xB0, 0xB1, 0xB2, 0xB3, 0xB4], pages

# An offset given by hand wins, for a panel that is not centred in the memory.
panel, bus = display(72, 40, x_offset=28)
assert panel.x_offset == 28
panel.fill(0)
panel.show(full_update=True)
assert (0x00, 0x0C) in column_commands(bus.commands) and (0x10, 0x01) in column_commands(bus.commands)

# A setup sequence is sent once, before the first frame is drawn.
panel, bus = display(72, 40, setup=PANEL_72X40)
sent = panel.startup
for index in range(len(PANEL_72X40)):
    assert sent[index] == PANEL_72X40[index], (index, sent[:len(PANEL_72X40)])
assert 0xA8 in PANEL_72X40 and PANEL_72X40[PANEL_72X40.index(0xA8) + 1] == 0x27, (
    "the multiplex ratio is the point of it: 40 rows, not the default 64"
)

# Without one, nothing is configured at all, which is what upstream does and what suits a
# panel whose defaults are already right.
panel, bus = display(128, 64)
assert not any(command in (0xA8, 0xD3) for command in panel.startup), panel.startup

print("sh1106: ok")
