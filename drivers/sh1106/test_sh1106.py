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
from sh1106 import PANEL_72X40, SH1106_I2C, panel_setup  # noqa: E402


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

# A setup sequence is sent once, and it has to be the last thing said before the first frame.
# flip() sets the scan direction the display offset is counted against, so a setup applied
# before it is applied to the wrong one and quietly does nothing.
panel, bus = display(72, 40, setup=PANEL_72X40)
sent = panel.startup


def position_of(sequence, inside):
    """Where a run of commands starts, or -1 if it was never sent as a run."""
    for start in range(len(inside) - len(sequence) + 1):
        if inside[start : start + len(sequence)] == list(sequence):
            return start
    return -1


at = position_of(PANEL_72X40, sent)
assert at >= 0, sent
assert 0xC0 in sent and sent.index(0xC0) < at, (
    "the scan direction is set before the panel setup, because the display offset is counted "
    "against it"
)
assert 0xAF in sent and sent.index(0xAF) < at, "and so is powering the panel on"
# The multiplex ratio is the point of the setup sequence: a 40 row panel driving 64 rows is
# dim and mapped to pages that are never written.
setup = panel_setup(40)
assert setup[0] == 0xA8 and setup[1] == 39, "40 rows, not the default 64"
assert panel_setup(40, contrast=0x80)[4] == 0x80, "contrast is settable"

# The boost converter that makes the voltage an OLED panel needs. Legible but dim, with the
# multiplex ratio already right, is what a panel without it looks like.
assert setup[-2:] == (0xAD, 0x8B), setup
assert panel_setup(40, dcdc=False)[-2:] != (0xAD, 0x8B), "and it can be left to an SSD1306"

# Where the rows sit is not in there: the driver owns it, because it changes with the scan
# direction, and a static list of commands cannot.
assert 0xD3 not in setup, setup
assert 0xA1 not in setup and 0xC8 not in setup, "orientation is flip()'s, not the setup's"


def pairs_of(command, commands):
    """Every value sent straight after `command`."""
    return [commands[index + 1] for index, value in enumerate(commands[:-1]) if value == command]


# Measured on a 72x40 panel: the picture lines up with the glass at 52, which is the 12 rows it
# sits into the 64 the controller scans, counted the way the un-flipped scan direction wants.
panel, bus = display(72, 40, setup=PANEL_72X40)
assert panel.y_offset == 52, panel.y_offset
assert pairs_of(0xD3, panel.startup) == [52], panel.startup
assert 0xC0 in panel.startup, "the un-flipped scan direction"

# Flipping mirrors the window as well as the scan, or a short panel falls off the screen: the
# same 12 rows are 64 - 12 from the other end.
bus.commands.clear()
panel.flip(True)
assert 0xC8 in bus.commands, "the scan direction reversed"
assert pairs_of(0xD3, bus.commands) == [12], bus.commands
bus.commands.clear()
panel.flip(False)
assert pairs_of(0xD3, bus.commands) == [52], "and back again"

# A full height panel has no offset either way round, which is why upstream never had to.
panel, bus = display(128, 64)
assert panel.y_offset == 0
assert pairs_of(0xD3, panel.startup) == [0], panel.startup
bus.commands.clear()
panel.flip(True)
assert pairs_of(0xD3, bus.commands) == [0], "0 mirrors to 0"

# A panel that is not centred can say so.
panel, bus = display(72, 40, y_offset=48)
assert pairs_of(0xD3, panel.startup) == [48]

# A setup sequence is sent once, and after flip(): the display offset is counted against the
# scan direction, so a setup applied before it is applied to the wrong one.
panel, bus = display(72, 40, setup=PANEL_72X40)
sent = panel.startup


def position_of(sequence, inside):
    """Where a run of commands starts, or -1 if it was never sent as a run."""
    for start in range(len(inside) - len(sequence) + 1):
        if inside[start : start + len(sequence)] == list(sequence):
            return start
    return -1


at = position_of(PANEL_72X40, sent)
assert at >= 0, sent
assert sent.index(0xC0) < at, "the scan direction is set first"
assert sent.index(0xAF) < at, "and so is powering the panel on"

print("sh1106: ok")
