# Driver for the rotary encoders with CLK, DT and SW pins: the KY-040 and every board like it.
#
# An encoder is not a potentiometer. It has no ends and no absolute position: it reports that it
# has been turned a notch, and in which direction, and it is up to your program to decide what
# that means. Turning it is what a volume knob or a menu wants; a potentiometer is what you use
# when a position on a dial has to mean something on its own.
#
# CLK and DT are two switches a quarter of a notch apart. Which of them changes first is the
# whole of how direction is worked out, which is why both are read on every edge of either.

from micropython import const
from time import ticks_diff, ticks_ms

# Indexed by the last two-bit state and the new one: (previous << 2) | current. A valid step
# gives 1 or -1, an impossible jump gives 0 and is thrown away, which is most of what makes a
# noisy encoder usable.
_TRANSITIONS = (0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0)


class RotaryEncoder:
    """A rotary encoder on `clk` and `dt`, with an optional push switch on `sw`.

    `value` counts detents, the notches you feel turning it. Most encoders take four quadrature
    steps per notch, which is what `steps_per_detent` is for: set it to 2 or 1 if yours counts
    two or four for every click you feel.

    Give `minimum` and `maximum` to keep the value inside a range, and `wrap=True` to make it
    run round the ends rather than stop at them, which is what a menu usually wants.
    """

    def __init__(self, clk, dt, sw=None, value=0, minimum=None, maximum=None, wrap=False,
                 steps_per_detent=4, reverse=False, debounce_ms=50):
        self._clk = clk
        self._dt = dt
        self._sw = sw
        clk.init(clk.IN, clk.PULL_UP)
        dt.init(dt.IN, dt.PULL_UP)
        if sw is not None:
            sw.init(sw.IN, sw.PULL_UP)

        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.wrap = wrap
        self.steps_per_detent = steps_per_detent
        self.reverse = reverse
        self.debounce_ms = debounce_ms

        self._state = (clk.value() << 1) | dt.value()
        self._substeps = 0
        self._pressed = False
        self._press_at = ticks_ms()
        self._press_pending = False

        trigger = clk.IRQ_RISING | clk.IRQ_FALLING
        clk.irq(handler=self._edge, trigger=trigger)
        dt.irq(handler=self._edge, trigger=trigger)

    def _edge(self, pin):
        # An interrupt handler: no allocation, and nothing that could raise.
        state = (self._clk.value() << 1) | self._dt.value()
        step = _TRANSITIONS[(self._state << 2) | state]
        self._state = state
        if not step:
            return  # a jump the encoder cannot really have made, so noise

        self._substeps += -step if self.reverse else step
        # One notch is several quadrature steps; only a whole notch moves the value.
        while self._substeps >= self.steps_per_detent:
            self._substeps -= self.steps_per_detent
            self._move(1)
        while self._substeps <= -self.steps_per_detent:
            self._substeps += self.steps_per_detent
            self._move(-1)

    def _move(self, direction):
        value = self.value + direction
        if self.minimum is not None and value < self.minimum:
            value = self.maximum if self.wrap and self.maximum is not None else self.minimum
        elif self.maximum is not None and value > self.maximum:
            value = self.minimum if self.wrap and self.minimum is not None else self.maximum
        self.value = value

    @property
    def pressed(self):
        """True while the switch is held down. The switch pulls the pin low, so this reads it."""
        return self._sw is not None and not self._sw.value()

    def was_pressed(self):
        """True once for each press of the switch, debounced. False if there is no switch."""
        if self._sw is None:
            return False
        pressed = not self._sw.value()
        now = ticks_ms()
        if pressed != self._pressed:
            # Either a real change or a contact bouncing; start the clock and see if it lasts.
            self._pressed = pressed
            self._press_at = now
            self._press_pending = pressed
        elif self._press_pending and ticks_diff(now, self._press_at) >= self.debounce_ms:
            self._press_pending = False
            return True
        return False
