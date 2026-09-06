# Seven Segment Display (74HC595) Example

In this example the microcontroller counts on a single 7-segment display and then runs through
the hex letters, driving all eight segments through a 74HC595 shift register. The digit needs
eight pins; the shift register does it with three, and chaining more digits costs no more pins.

## Requires
This example needs the [74HC595 shift register](../../drivers/sr74hc595) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Three pins to the shift register, and two pins on the register that are easy to forget: OE must
be tied to ground or nothing lights up at all, and MR must be tied high or the register keeps
clearing itself.

| 74HC595 | Goes to |
| --- | --- |
| DS (14) | GPIO 13 |
| SHCP (11) | GPIO 14 |
| STCP (12) | GPIO 12 |
| OE (13) | GND |
| MR (10) | 3.3V |
| VCC (16) | 3.3V |
| GND (8) | GND |
| Q0 to Q7 (15, 1-7) | segments a, b, c, d, e, f, g, dp, each through its own resistor |

Every segment needs its own series resistor, around 220Ω to 330Ω for a 3.3V supply. One resistor
on the shared common pin looks like it works, but the digit then changes brightness depending on
how many segments are lit.

The common pin of the display goes to ground for a common cathode digit, which is what the
script assumes. For a common anode digit, take the common pin to 3.3V and set
`common_anode = True` at the top of the script.

## Output

The digit counts `0` to `9`, then shows `a` to `f` with the decimal point lit, then blanks and
starts again. The console prints along with it, so you can tell the script is running before the
wiring is right.

## If the wrong segments light

The script maps shift register outputs to segments with `SEGMENT_ORDER` near the top, assuming
Q0 to Q7 are wired to a, b, c, d, e, f, g, dp in that order. Wired differently, reorder that
tuple to match your board rather than editing the digit table below it.

A digit that shows the negative of what it should — everything lit except the right segments —
is a common anode display: set `common_anode = True`.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
