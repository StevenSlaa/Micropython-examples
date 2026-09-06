---
driver: rotary
author: Steven Slaa
---

# Rotary encoder (KY-040)

Reads the rotary encoders with CLK, DT and SW pins — the KY-040 and the many boards like it,
including the ones with a knob on top and a switch underneath.

## An encoder is not a potentiometer

A potentiometer has ends, and its position means something on its own: turn it to the same place
and you get the same number back. An encoder has neither. It has no ends, no absolute position,
and it can be turned forever. All it reports is *that it moved a notch, and which way*.

That is exactly what a volume control or a menu wants, and it is why the driver keeps a `value`
that your program owns and can set to anything at any time. It is the wrong part for reading a
dial position; that is a [potentiometer](../../examples/analog-read).

## Install

Install it from the Pulsar IoT library panel, or copy `rotary.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from rotary import RotaryEncoder

knob = RotaryEncoder(clk=Pin(13), dt=Pin(12), sw=Pin(14), value=0, minimum=0, maximum=100)

while True:
    print(knob.value)
    if knob.was_pressed():
        knob.value = 0
```

Turning is handled by interrupts, so nothing needs to be polled quickly and the loop is free to
be slow. `value` is simply a number you can read whenever you like — and write, when something
else should change it.

For a menu that runs round the ends rather than stopping at them:

```python
menu = RotaryEncoder(Pin(13), Pin(12), value=0, minimum=0, maximum=3, wrap=True)
```

## Wiring

| Encoder | Goes to |
| --- | --- |
| CLK | any GPIO |
| DT | any GPIO |
| SW | any GPIO, or leave it out |
| + | 3.3V |
| GND | GND |

No pull-up resistors are needed: the driver turns the board's own on for all three pins. Some
KY-040 boards have their own pull-ups fitted, which does no harm.

## When it counts wrong

These modules are cheap and their contacts are noisy, and nearly every complaint about them is
one of these three:

| What happens | What to change |
| --- | --- |
| It counts backwards | `reverse=True`, or swap the CLK and DT wires |
| One click moves the value by four | `steps_per_detent` is wrong for your encoder — try 1 |
| One click moves it by two, or every other click does nothing | try `steps_per_detent=2` |

Four quadrature steps per detent is much the most common, which is why it is the default. What
the number really means is how many electrical steps the encoder produces for each notch you can
feel, and the manufacturers do not agree on it.

Steps that could not have happened — the encoder claiming to have jumped two states at once —
are thrown away rather than counted. That is most of what makes a noisy encoder usable, and it
is why the value does not jitter when the knob is merely knocked.

## Notes

- The switch is separate from the turning, and needs no wiring of its own beyond the pin.
  `pressed` is true while it is held; `was_pressed()` is true once per press, debounced.
- `was_pressed()` has to be called from your loop to notice anything, and a press is confirmed
  on the call after the one that first saw it. Calling it often is free.
- `value` is yours: set it, and the encoder counts on from there.
- Turning very fast can still lose a notch, because the interrupt has to keep up with the
  contacts. It is not usually noticeable by hand.
- The press switch has no interrupt of its own here. If a press must never be missed, put a
  separate `Pin.irq` on the SW pin.

## Tests

`python3 -B drivers/rotary/test_rotary.py` wires fake pins as a real quadrature encoder, so a
simulated turn walks CLK and DT through their four states, and checks direction, detents,
ranges, wrapping, noise rejection and the switch, off-board.

Used by: [rotary-encoder](../../examples/rotary-encoder)
