# Rotary Encoder

In this example the microcontroller reads a rotary encoder: turning the knob moves a number up
and down within a range, and pressing the knob resets it.

## Requires
This example needs the [Rotary encoder (KY-040)](../../drivers/rotary) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

No resistors needed: the driver turns on the board's own pull-ups for all three pins.

| Encoder | ESP32 | Pico |
| --- | --- | --- |
| CLK | 13 | 10 |
| DT | 12 | 11 |
| SW | 14 | 12 |
| + | 3V3 | 3V3 |
| GND | GND | GND |

Some boards label the pins A and B instead of CLK and DT; they are the same two. SW can be left
unwired if your encoder has no switch — pass `sw=None` and the press simply never happens.

## Output
```
Turn the knob, and press it to reset to 50
Value:  51  ##########
Value:  52  ##########
Value:  53  ##########
Value:  55  ###########
Reset
Value:  50  ##########
```

Nothing is printed while the knob is still, because the value has not changed. The bar is there
because a number is hard to judge by eye while you are turning something.

## How this differs from a potentiometer

A [potentiometer](../analog-read) has ends, and its position is the value: turn it back to the
same place and you read the same number. An encoder has no ends and no position at all. It
reports only that it moved a notch and which way, and the program decides what that means —
which is why the value here starts at 50 rather than wherever the knob happens to be sitting.

That is also why the knob can be turned forever, and why pressing it can reset the number to
anything without the knob and the value disagreeing afterwards.

## If it counts wrong

| What happens | What to change |
| --- | --- |
| It counts backwards | `reverse = True`, or swap the CLK and DT wires |
| One click moves it by four | `steps_per_detent = 1` |
| One click moves it by two | `steps_per_detent = 2` |
| It jumps around while you turn slowly | usually a bad module; try the other detent settings first |

## Plotter

Open the **Plotter** tab beside the REPL and turn the knob. The value draws a line that follows
your hand, flat while you are not touching it, and drops straight back to 50 when you press.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
