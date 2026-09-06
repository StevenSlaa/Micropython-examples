---
driver: keypad
author: Steven Slaa
---

# Matrix keypad

Reads the flat membrane keypads: the 4x4 with eight pins and the 4x3 with seven.

There is no chip in one of these. Under each key is a switch joining one row wire to one column
wire, so the driver drives each row low in turn and watches which column follows it down.

## Install

Install it from the Pulsar IoT library panel, or copy `keypad.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from keypad import Keypad

rows = [Pin(pin) for pin in (13, 12, 14, 27)]
columns = [Pin(pin) for pin in (26, 25, 33, 32)]
pad = Keypad(rows, columns)

while True:
    key = pad.read()
    if key:
        print("pressed", key)
```

`read()` is debounced and reports each press once, however long the key is held. Call it as
often as you like — it does its own timing, and needs no sleep in the loop.

For keys held down, such as a game, ask what is down right now instead:

```python
held = pad.scan()      # ['4', '6'] while both are held
```

## Wiring

Any eight GPIO pins. Rows are driven and columns are read, so the two lists are not
interchangeable — but no harm comes of getting them the wrong way round, and the symptom is
obvious: every key reports as a different one in a tidy pattern. Swap the two lists.

Looking at a 4x4 keypad's ribbon from the front, the pins are usually rows 1-4 then columns 1-4,
left to right. Nothing is standard here, so if the labels come out shuffled, the wiring is not
what the driver assumes: change the pin order rather than the code.

No pull-up resistors are needed. The driver turns the board's own on for the column pins.

## Notes

- **Three keys at once can invent a fourth.** With no diodes in the keypad, three keys forming
  three corners of a rectangle let current reach the fourth corner, and it reads as pressed. Two
  at a time is always safe; more needs a keypad with diodes.
- `keys` takes a grid of labels for a keypad printed differently, and they do not have to be
  single characters: `Keypad(rows, columns, keys=(("yes", "no"),))` works.
- A key press is reported once. If you want it to repeat while held, `scan()` gives you the raw
  state to do that yourself.
- `debounce_ms` defaults to 25, which suits membrane keypads. A worn keypad or long wires may
  want more; the cost is a slower response.
- The release is debounced as well as the press, so the same key can be reported again only
  after it has been seen up for that long. That is what stops one press being counted twice.

## Tests

`python3 -B drivers/keypad/test_keypad.py` wires fake pins into a real matrix, so a simulated
press really does pull a column down, and checks the labels, the debounce and a bouncing
contact, off-board.

Used by: [keypad-4x4](../../examples/keypad-4x4)
