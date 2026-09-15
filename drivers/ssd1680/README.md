---
driver: ssd1680
author: Steven Slaa
---

# SSD1680 e-paper (2.9 inch, black/white/red)

## What it is

E-paper, or electronic paper, is the kind of screen an e-reader has. Every pixel is a tiny
capsule of coloured particles suspended in liquid, and a voltage pulls the black, white or red
particles to the front. Once they are there they stay, **without power**: the image remains on the
screen after you unplug the board, for days or years. It is easy to read in sunlight, uses power
only while it changes, and has no backlight.

The price is speed. A black, white and red panel takes about **25 seconds** to refresh, and the
whole screen flashes black, white and red while it does. That is what it is supposed to do. It is
a display for things that change every few minutes, not every second: a weather station, a name
badge, a price label, a to-do list.

This driver is for 2.9 inch, 128 by 296 pixel panels on the Solomon Systech **SSD1680**
controller, like the WeAct Studio 2.9 inch module.

| | |
| --- | --- |
| Size | 2.9 inch, 128 × 296 pixels |
| Colours | black, white and red |
| Controller | SSD1680 |
| Interface | SPI, plus D/C, RES and BUSY pins |
| Supply | 3.3V |
| Full refresh | about 25 seconds (23.6 measured on a WeAct module at room temperature) |
| Memory used | two images of 4.7KB each |

## Wiring

The module has eight pins. SDA and SCL are SPI data and clock here, not I2C, whatever the labels
suggest.

| Module | What it does | Pico | XIAO RP2040 | ESP32 | ESP32-S3 |
| --- | --- | --- | --- | --- | --- |
| VCC | 3.3V power | 3V3(OUT) | 3V3 | 3V3 | 3V3 |
| GND | ground | GND | GND | GND | GND |
| SDA | SPI data (MOSI) | GP11 | D10 (GPIO3) | 23 | 11 |
| SCL | SPI clock (SCK) | GP10 | D8 (GPIO2) | 18 | 12 |
| CS | chip select | GP13 | D5 (GPIO7) | 5 | 10 |
| D/C | command or data | GP14 | D6 (GPIO0) | 17 | 9 |
| RES | reset | GP15 | D7 (GPIO1) | 16 | 8 |
| BUSY | busy signal back to the board | GP12 | D9 (GPIO4) | 4 | 7 |

The Pico pins are physical pins 14 to 20 in a row, with GND at pin 18. Use SPI 1 on a Pico, SPI 0
on a XIAO RP2040 (`SPI(0, sck=Pin(2), mosi=Pin(3))`) and SPI 2 on an ESP32.

## Install

Install it from the Pulsar IoT library panel, or copy `ssd1680.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SPI
from ssd1680 import SSD1680, WHITE, BLACK, RED

spi = SPI(1, baudrate=4000000, sck=Pin(10), mosi=Pin(11))
display = SSD1680(spi, cs=Pin(13), dc=Pin(14), rst=Pin(15), busy=Pin(12))

display.fill(WHITE)
display.text("Hello", 10, 10, BLACK, scale=3)
display.rect(0, 100, 296, 28, RED, fill=True)
display.show()              # about 25 seconds
```

Nothing appears until `show()`. Draw everything first, then show it once.

| Method | Draws |
| --- | --- |
| `fill(color)` | the whole screen |
| `pixel(x, y, color)` | one pixel |
| `hline(x, y, width, color)`, `vline(x, y, height, color)` | a straight line |
| `line(x1, y1, x2, y2, color)` | a line at any angle |
| `rect(x, y, width, height, color, fill=False)` | a rectangle, outline or filled |
| `ellipse(x, y, x_radius, y_radius, color, fill=False)` | a circle or ellipse around x, y |
| `text(string, x, y, color=BLACK, scale=1)` | text in the 8 × 8 pixel built-in font, `scale` times larger |
| `bitmap(data, x, y, width, height, color=BLACK)` | a 1 bit image such as a logo (`MONO_HLSB` bytes): 1 bits in `color`, 0 bits left as they are |
| `show()` | puts it all on the screen |

Colours are `WHITE`, `BLACK` and `RED`. `display.width` and `display.height` give the size for
the rotation in use.

## Rotation

`rotation=270` (the default) and `rotation=90` are landscape, 296 wide and 128 high; `0` and `180`
are portrait, 128 wide and 296 high. 270 is the right way up on the WeAct module it was tested
with. If the picture comes out upside down on yours, use the other one of the pair.

## Notes

- **Wait at least 3 minutes between refreshes.** Makers of three colour panels ask for that,
  because refreshing more often wears the red particles out and leaves ghosts. Nothing stops you,
  but a clock with seconds on it is not a job for this screen.
- **No partial refresh.** Black and white panels can update part of the screen quickly; three
  colour ones always redraw everything, flashing included.
- **Every `show()` starts with a hardware reset and ends in deep sleep.** A glitch or an
  interrupted refresh cannot leave the controller confused for the next one, and the panel never
  sits with its high voltage switched on. Between refreshes it draws next to nothing.
- **If BUSY never goes low, `show()` raises an error** after `busy_timeout_ms` (60 seconds)
  instead of hanging. That almost always means a wire: BUSY, RES or power.
- **Keep it between 0 and 50°C** while refreshing. In the cold, red takes longer and can come out
  pale.
- **Clear it to white before storing the module** for a long time.
- The built-in font is 8 × 8 pixels, which is small on this screen: `scale=2` or `3` is easier to
  read.

## Tests

`python3 -B drivers/ssd1680/test_ssd1680.py` checks the colour bits, all four rotations against a
pixel by pixel map, the refresh command sequence, the BUSY timeout and scaled text, off-board.

The command sequence follows [GxEPD2](https://github.com/ZinggJM/GxEPD2) by Jean-Marc Zingg,
`GxEPD2_290_C90c`, the Arduino driver for this panel.

Used by: [spi-epaper-ssd1680](../../examples/spi-epaper-ssd1680)
