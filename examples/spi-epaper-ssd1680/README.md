---
example: spi-epaper-ssd1680
author: Steven Slaa
---

# 2.9 inch E-paper (black/white/red) Example

In this example the microcontroller draws an illustrative dashboard in black, white and red on a
2.9 inch e-paper display, such as the WeAct Studio module: the Pulsar IoT logo, three cards with
readings and a chart, redrawn every three minutes.

E-paper keeps its image without power, like printed paper: unplug the board and the picture
stays. The price is speed, since a three colour refresh takes about 25 seconds. The
[driver README](../../drivers/ssd1680) explains more.

## Requires
This example needs the [SSD1680 e-paper (2.9 inch, black/white/red)](../../drivers/ssd1680)
driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The script picks the pins for your board by itself, so wire it like this and it runs as it is.
The one exception is the Seeed XIAO RP2040, which runs the same firmware as a Pico: on a XIAO,
remove the `#` in front of `board = "xiao-rp2040"` near the top of the script. SDA and SCL are SPI
here, not I2C, despite the names.

| Display | Pico | XIAO RP2040 | ESP32 | ESP32-S3 |
| --- | --- | --- | --- | --- |
| VCC | 3V3(OUT), pin 36 | 3V3 | 3V3 | 3V3 |
| GND | GND, pin 18 | GND | GND | GND |
| SDA | GP11, pin 15 | D10 (GPIO3) | 23 | 11 |
| SCL | GP10, pin 14 | D8 (GPIO2) | 18 | 12 |
| CS | GP13, pin 17 | D5 (GPIO7) | 5 | 10 |
| D/C | GP14, pin 19 | D6 (GPIO0) | 17 | 9 |
| RES | GP15, pin 20 | D7 (GPIO1) | 16 | 8 |
| BUSY | GP12, pin 16 | D9 (GPIO4) | 4 | 7 |

On the XIAO, with the USB connector at the top, six wires go to the right-hand side (3V3, GND,
D10, D9, D8, D7) and two to the bottom of the left-hand side (D5, D6).

**Use 3.3V, not 5V.** On a Pico that is 3V3(OUT), pin 36, not VBUS or VSYS.

## What happens

1. The script prints `Refreshing...` and the screen flashes black, white and red for about 25
   seconds. That flashing is how three colour e-paper works; it is not a fault.
2. A dashboard appears, the way the screen of a Pulsar IoT device could look: the logo at the
   top left with a red **ONLINE** label, cards with temperature, humidity and battery, and a chart
   of the last 24 hours with the latest reading in red.
3. Every three minutes it refreshes, with the numbers moved a little.

The readings are made up; nothing is measured. The example is a picture of a user interface, to
show what the drawing methods can build. Put real sensor readings in `temperature`, `humidity`,
`battery` and `history` and it becomes a real dashboard.

Unplug the board after a refresh and the picture stays.

## The artwork

`pulsar_ui.py`, next to the script, holds the artwork as 1 bit bitmaps: the logo on one line, and
large Poppins characters for the numbers. Both were made on a computer from the logo's SVG and the
Poppins font, because the board has neither a vector renderer nor fonts. The script draws them
with `display.bitmap()`. Everything else, the cards, lines, chart, battery symbol and small text,
is drawn with the driver's own methods.

Any black and white image works the same way: turn it into `MONO_HLSB` bytes, 8 pixels a byte,
and pass them to `bitmap()` with a width, a height and a colour. The IDE copies `pulsar_ui.py` to
the board together with the script.

## Output
```
Refreshing, the screen will flash for about 25 seconds...
Refresh: 23.8 s
```

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| `The e-paper stayed busy...` after 60 seconds | BUSY is on the wrong pin, or the display has no power. Check VCC, GND, BUSY and RES |
| No error, but the screen never changes | SDA and SCL swapped, or CS or D/C on the wrong pin |
| The picture is upside down | set `rotation = 90` instead of 270 |
| The picture is cut off or squashed | `rotation` is 0 or 180, which is portrait; use 90 or 270 |
| Red looks pale or pinkish | too cold, or refreshed too often. Keep it above about 10°C and wait the full 3 minutes |

## Plotter

The only number printed is how long each refresh took, so the plotter draws a nearly flat line
around 24 seconds. A refresh that gets slower over time usually means the room got colder.

## Tested
- Seeed XIAO RP2040 running MicroPython 1.28.0 (the Pico firmware), with the WeAct Studio 2.9
  inch black/white/red module wired as in the XIAO column above. A refresh took 23.6 to 23.8
  seconds at room temperature, and black, white and red all came out correctly with
  `rotation = 270`.
