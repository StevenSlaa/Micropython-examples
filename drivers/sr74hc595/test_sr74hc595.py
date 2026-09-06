# Run with: python3 -B drivers/sr74hc595/test_sr74hc595.py
# Fake pins that record every edge, so the bit order, the chain order and the latching can be
# read back exactly as a logic analyser would see them.
from sr74hc595 import ShiftRegister


class _Pin:
    OUT = 3

    def __init__(self):
        self.level = 0
        self.history = []

    def init(self, mode, value=0):
        self.level = value

    def __call__(self, level):
        self.level = level
        self.history.append(level)


def wire(count=1, **kwargs):
    data, clock, latch = _Pin(), _Pin(), _Pin()
    register = ShiftRegister(data, clock, latch, count, **kwargs)
    for pin in (data, clock, latch):
        pin.history.clear()  # drop the blanking write the constructor does
    return register, data, clock, latch


def shifted(data, clock):
    """The bits the register saw, sampled the way the chip does: on each rising clock edge."""
    bits = []
    level = 0
    for index, edge in enumerate(clock.history):
        if edge == 1 and level == 0:
            bits.append(data.history[index // 2])
        level = edge
    return bits


register, data, clock, latch = wire()
register.write(0b10110010)
assert shifted(data, clock) == [1, 0, 1, 1, 0, 0, 1, 0], "most significant bit first"
assert latch.history == [1, 0], "one latch pulse, after the whole byte"
assert len(clock.history) == 16, "eight bits, each a rise and a fall"

# Least significant bit first, for a board wired the other way round.
register, data, clock, _ = wire(msb_first=False)
register.write(0b10110010)
assert shifted(data, clock) == [0, 1, 0, 0, 1, 1, 0, 1], "reversed"

# Chained: the far register's byte has to be shifted out first to end up there.
register, data, clock, latch = wire(count=2)
register.write([0xF0, 0x0F])
assert shifted(data, clock) == [0, 0, 0, 0, 1, 1, 1, 1] + [1, 1, 1, 1, 0, 0, 0, 0]
assert latch.history == [1, 0], "the whole chain latches once, so it updates together"
try:
    register.write([0x01])
    raise AssertionError("the wrong number of bytes must be refused")
except ValueError:
    pass

# Single outputs are numbered from QA of the first register, across the chain.
register, _, _, _ = wire(count=2)
register.pin(0)
register.pin(9)
assert register[0] == 0b00000001 and register[1] == 0b00000010, (register[0], register[1])
register.pin(0, False)
assert register[0] == 0 and register[1] == 0b00000010, "turning one off leaves the rest"
register[1] = 0xFF
assert register[1] == 0xFF
register.clear()
assert register[0] == 0 and register[1] == 0

print("sr74hc595: ok")
