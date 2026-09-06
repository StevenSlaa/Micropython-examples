# Driver for the membrane matrix keypads: the flat 4x4 with eight pins and the 4x3 with seven.
#
# There is no chip in one of these. Under each key is a switch joining one row wire to one
# column wire, so finding out which key is down means driving each row low in turn and seeing
# which column follows it down. That is what scan() does.

from time import sleep_us, ticks_diff, ticks_ms

KEYS_4X4 = (
    ("1", "2", "3", "A"),
    ("4", "5", "6", "B"),
    ("7", "8", "9", "C"),
    ("*", "0", "#", "D"),
)

KEYS_4X3 = (
    ("1", "2", "3"),
    ("4", "5", "6"),
    ("7", "8", "9"),
    ("*", "0", "#"),
)


class Keypad:
    """A matrix keypad on a list of row pins and a list of column pins.

    Rows are driven, columns are read, which is why the two lists are not interchangeable. If
    every key reads as the wrong one in a tidy pattern, the two are swapped.

    `keys` is a grid of labels matching the wiring; the 4x4 and 4x3 defaults suit the keypads
    sold with those labels printed on them.
    """

    def __init__(self, rows, columns, keys=None, debounce_ms=25):
        self.rows = rows
        self.columns = columns
        self.keys = keys or (KEYS_4X4 if len(columns) == 4 else KEYS_4X3)
        self.debounce_ms = debounce_ms
        for pin in rows:
            pin.init(pin.OUT, value=1)
        for pin in columns:
            # Idle high, so a key press is what pulls one low.
            pin.init(pin.IN, pin.PULL_UP)
        self._candidate = None
        self._settled = None
        self._changed = ticks_ms()

    def scan(self):
        """Every key held down right now, as a list of labels.

        Three keys at once can invent a fourth that nobody is touching: with no diodes in the
        keypad, current finds its way around the square those keys make. Two at a time is safe.
        """
        held = []
        for row_index, row in enumerate(self.rows):
            row(0)
            sleep_us(5)  # let a long ribbon cable settle before reading
            for column_index, column in enumerate(self.columns):
                if not column.value():
                    held.append(self.keys[row_index][column_index])
            row(1)
        return held

    def read(self):
        """The key pressed since the last call, or None.

        Debounced, and reported once: holding a key down does not repeat it. Call it as often
        as you like; it does the timing itself.
        """
        held = self.scan()
        key = held[0] if held else None
        now = ticks_ms()

        if key != self._candidate:
            # Either a real change or a contact bouncing. Start the clock and see if it lasts.
            self._candidate = key
            self._changed = now
            return None
        if key == self._settled:
            return None  # already reported, and still held
        if ticks_diff(now, self._changed) < self.debounce_ms:
            return None
        self._settled = key
        return key
