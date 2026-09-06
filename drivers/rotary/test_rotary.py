# Run with: python3 -B drivers/rotary/test_rotary.py
# Fake pins wired as a quadrature encoder, so turning the knob really does walk CLK and DT
# through their four states and the interrupt handler runs on every edge of either.
import sys, types

clock = [0]
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["time"] = types.SimpleNamespace(
    ticks_ms=lambda: clock[0], ticks_diff=lambda a, b: a - b
)
from rotary import RotaryEncoder  # noqa: E402


class _Pin:
    IN = 1
    PULL_UP = 2
    IRQ_RISING = 4
    IRQ_FALLING = 8

    def __init__(self, level=1):
        self.level = level
        self.handler = None

    def init(self, mode, pull=None):
        pass

    def irq(self, handler, trigger):
        self.handler = handler

    def value(self):
        return self.level


class _Knob:
    """CLK and DT, and the four states one notch of turning walks through."""

    # A quarter turn of the shaft, in (clk, dt) pairs. Both idle high on these boards.
    STATES = ((1, 1), (0, 1), (0, 0), (1, 0))

    def __init__(self, **kwargs):
        self.clk, self.dt, self.sw = _Pin(), _Pin(), _Pin()
        self.encoder = RotaryEncoder(self.clk, self.dt, self.sw, **kwargs)
        self._position = 0

    def _set(self, clk, dt):
        # Each pin that changes fires the handler, exactly as the hardware would.
        for pin, level in ((self.clk, clk), (self.dt, dt)):
            if pin.level != level:
                pin.level = level
                pin.handler(pin)

    def turn(self, detents, steps_per_detent=4):
        """Turns the knob, one quadrature step at a time."""
        direction = 1 if detents >= 0 else -1
        for _ in range(abs(detents) * steps_per_detent):
            self._position = (self._position + direction) % 4
            self._set(*self.STATES[self._position])

    def press(self, down=True):
        self.sw.level = 0 if down else 1


# One notch one way, one notch back.
knob = _Knob()
knob.turn(1)
assert knob.encoder.value == 1, knob.encoder.value
knob.turn(-1)
assert knob.encoder.value == 0

# Several notches, and the direction is consistent rather than merely changing.
knob = _Knob()
knob.turn(5)
assert knob.encoder.value == 5
knob.turn(-8)
assert knob.encoder.value == -3

# Part of a notch does not count. Only whole clicks move the value.
knob = _Knob()
knob.turn(1, steps_per_detent=3)  # three of the four steps
assert knob.encoder.value == 0, "a partial notch is not a notch"
knob.turn(1, steps_per_detent=1)  # the fourth
assert knob.encoder.value == 1

# reverse=True for an encoder wired the other way round, or that simply counts backwards.
knob = _Knob(reverse=True)
knob.turn(2)
assert knob.encoder.value == -2

# An encoder that gives two steps per click rather than four.
knob = _Knob(steps_per_detent=2)
knob.turn(1, steps_per_detent=2)
assert knob.encoder.value == 1

# A range that stops at the ends, for a setting.
knob = _Knob(value=8, minimum=0, maximum=10)
knob.turn(5)
assert knob.encoder.value == 10, "it stops at the top"
knob.turn(-20)
assert knob.encoder.value == 0, "and at the bottom"

# A range that runs round, for a menu.
knob = _Knob(value=2, minimum=0, maximum=2, wrap=True)
knob.turn(1)
assert knob.encoder.value == 0, "past the top comes back to the bottom"
knob.turn(-1)
assert knob.encoder.value == 2, "and the other way round"

# Noise on one pin is not a step: the state it claims to have jumped to is impossible.
knob = _Knob()
for _ in range(6):
    knob.clk.level ^= 1
    knob.clk.handler(knob.clk)
    knob.clk.level ^= 1
    knob.clk.handler(knob.clk)
assert knob.encoder.value == 0, "a pin flapping on its own moves nothing"

# The switch: held is not the same as pressed once.
knob = _Knob(debounce_ms=50)
clock[0] = 0
assert not knob.encoder.pressed and not knob.encoder.was_pressed()
knob.press()
assert knob.encoder.pressed, "held down"
assert not knob.encoder.was_pressed(), "not yet: it might be a bounce"
clock[0] += 60
assert knob.encoder.was_pressed(), "settled, so it counts"
assert not knob.encoder.was_pressed(), "and only once, however long it is held"
knob.press(False)
assert not knob.encoder.was_pressed(), "a release is not a press"
knob.press()
assert not knob.encoder.was_pressed(), "the new press starts its own clock"
clock[0] += 60
assert knob.encoder.was_pressed(), "and counts once it has settled"

# An encoder with no switch answers politely rather than raising.
plain = RotaryEncoder(_Pin(), _Pin())
assert plain.pressed is False and plain.was_pressed() is False

print("rotary: ok")
