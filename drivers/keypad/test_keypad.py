# Run with: python3 -B drivers/keypad/test_keypad.py
# A simulated keypad: fake pins wired into a matrix, so pressing a key really does pull a
# column down while its row is driven low, and a fake clock so the debounce can be watched.
import sys, types

clock = [0]
sys.modules["time"] = types.SimpleNamespace(
    ticks_ms=lambda: clock[0],
    ticks_diff=lambda a, b: a - b,
    sleep_us=lambda us: None,
)
from keypad import KEYS_4X3, KEYS_4X4, Keypad  # noqa: E402


class _RowPin:
    OUT = 3
    IN = 1
    PULL_UP = 2

    def __init__(self):
        self.level = 1

    def init(self, mode, pull=None, value=None):
        if value is not None:
            self.level = value

    def __call__(self, level):
        self.level = level


class _ColumnPin(_RowPin):
    def __init__(self, matrix, index):
        super().__init__()
        self.matrix = matrix
        self.index = index

    def value(self):
        # A key joins its row wire to its column wire, so the column follows a row that is low.
        for row, column in self.matrix.pressed:
            if column == self.index and self.matrix.rows[row].level == 0:
                return 0
        return 1


class _Keypad:
    def __init__(self, rows=4, columns=4, **kwargs):
        self.pressed = set()
        self.rows = [_RowPin() for _ in range(rows)]
        self.columns = [_ColumnPin(self, index) for index in range(columns)]
        self.keypad = Keypad(self.rows, self.columns, **kwargs)

    def press(self, *keys):
        self.pressed = set(keys)


pad = _Keypad()
assert pad.keypad.scan() == [], "nothing held to start with"
assert all(row.level == 1 for row in pad.rows), "rows idle high"

# Row 1, column 2 is the key labelled 6 on a 4x4 keypad.
pad.press((1, 2))
assert pad.keypad.scan() == ["6"], pad.keypad.scan()
pad.press((0, 0), (3, 3))
assert pad.keypad.scan() == ["1", "D"], "two keys at once are both seen"
assert all(row.level == 1 for row in pad.rows), "the rows are left high again after a scan"

# A 4x3 keypad has its own labels, chosen from the number of columns.
narrow = _Keypad(columns=3)
assert narrow.keypad.keys == KEYS_4X3
narrow.press((3, 0))
assert narrow.keypad.scan() == ["*"]
assert _Keypad().keypad.keys == KEYS_4X4

# A label grid of your own, for a keypad with different printing.
custom = _Keypad(rows=1, columns=2, keys=(("yes", "no"),))
custom.press((0, 1))
assert custom.keypad.scan() == ["no"]

# read() waits out the debounce, reports once, and does not repeat while the key is held.
clock[0] = 0
pad = _Keypad(debounce_ms=25)
pad.press((0, 1))
assert pad.keypad.read() is None, "the first sight of a key is not trusted yet"
clock[0] += 10
assert pad.keypad.read() is None, "still inside the debounce window"
clock[0] += 20
assert pad.keypad.read() == "2", "settled, so now it counts"
clock[0] += 100
assert pad.keypad.read() is None, "holding it down does not repeat it"

# Releasing and pressing the same key again is a second press. The release has to settle
# first, exactly as a press does, or a bouncy contact would report itself twice.
pad.press()
clock[0] += 30
assert pad.keypad.read() is None, "a release is not a key"
clock[0] += 30
assert pad.keypad.read() is None, "and the release settles here, without reporting anything"
pad.press((0, 1))
assert pad.keypad.read() is None
clock[0] += 30
assert pad.keypad.read() == "2", "pressed again"

# A contact bouncing on and off inside the window reports nothing at all.
clock[0] = 1000
pad = _Keypad(debounce_ms=25)
for bounce in range(6):
    pad.press((2, 2)) if bounce % 2 == 0 else pad.press()
    clock[0] += 5
    assert pad.keypad.read() is None, "bouncing is not a press"
pad.press((2, 2))
clock[0] += 5
pad.keypad.read()
clock[0] += 30
assert pad.keypad.read() == "9", "once it settles, it counts once"

print("keypad: ok")
