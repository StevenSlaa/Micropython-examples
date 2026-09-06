# 74HC595 shift register

Turns three GPIO pins into eight outputs, or sixteen, or more: the 74HC595 takes bits in
serially and presents them on eight parallel pins, and chaining them costs no extra pins at all.
Useful for LEDs, a 7-segment display, or anything else that needs more outputs than the board
has to spare.

The module is called `sr74hc595` because a Python module name cannot start with a digit.

## Install

Install it from the Pulsar IoT library panel, or copy `sr74hc595.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from sr74hc595 import ShiftRegister

outputs = ShiftRegister(data=Pin(13), clock=Pin(14), latch=Pin(12))

outputs.write(0b10110010)   # all eight at once
outputs.pin(3)              # just Q3 on
outputs.pin(3, False)       # and off again
outputs.clear()
```

Chained registers are one long row of outputs:

```python
outputs = ShiftRegister(Pin(13), Pin(14), Pin(12), count=2)

outputs.write([0xFF, 0x00])   # first register all on, second all off
outputs.pin(9)                # Q1 of the second register
outputs[1] = 0b00001111       # or set a whole register
```

## Wiring

| 74HC595 | Goes to |
| --- | --- |
| DS (14), also called SER | data pin |
| SHCP (11), SRCLK | clock pin |
| STCP (12), RCLK | latch pin |
| OE (13) | GND, so the outputs are enabled |
| MR (10), SRCLR | 3.3V, so the register is not held clear |
| VCC (16), GND (8) | 3.3V and ground |
| Q7S (9) | DS of the next register, when chaining |

Leaving OE floating means nothing lights up, and leaving MR floating gives output that flickers
or never appears. They are the two pins people forget.

## Notes

- Outputs only change when the latch pulses, so a chain updates in one go instead of visibly
  rippling. The driver latches once per `write()`.
- Each output can drive about 20mA, and the whole chip about 70mA total, so LEDs need their
  series resistors and eight bright ones at once is already at the limit. A 7-segment digit is
  fine; a row of high power LEDs is not.
- `msb_first=False` if your outputs come out back to front. Which way round a board wants
  depends on how the outputs were wired to whatever they drive.
- Shifting is bit banged, at a few kHz. That is plenty for a display a person is reading, but if
  you need to push frames, wire DS to MOSI and SHCP to SCK and drive them from `machine.SPI`
  instead, latching by hand.
- The 74HC595 has no way to be read back, so the driver keeps its own copy of what it wrote.
  That copy is what `pin()` and `outputs[n]` work from.

## Tests

`python3 -B drivers/sr74hc595/test_sr74hc595.py` checks the bit order, the chain order and the
latching by recording every pin edge, off-board.

Used by: [seven-segment-74hc595](../../examples/seven-segment-74hc595)
