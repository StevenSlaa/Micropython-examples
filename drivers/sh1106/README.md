---
driver: sh1106
author: Robert Hammelrath
---

# SH1106 OLED

Driver for SH1106 OLED panels. It looks like an [SSD1306](../ssd1306), is sold as one, and is
not one — which is why this driver exists.

Use it for the 1.3 inch modules, and for the 0.42 inch display built into the ESP32-C3 SuperMini.

## How to tell it from an SSD1306

Both take the same commands to set up, so an SSD1306 driver will initialise an SH1106 quite
happily. What differs is how the pixels are sent:

- The **SSD1306** supports *horizontal addressing*: send the whole frame in one go, and the
  controller runs on from one page to the next.
- The **SH1106** does not. It ignores that command, stays in page addressing, and wraps back to
  the start of the **same page**.

So an SSD1306 driver on an SH1106 dumps the entire frame into page 0, over and over. That gives
one very recognisable symptom:

> **The top eight rows are right and everything below them is noise.**

Page 0 gets the picture, pages 1 and up are never written and keep whatever they powered up
with. If that is what you are looking at, this is your driver.

## Install

Install it from the Pulsar IoT library panel, or copy `sh1106.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from sh1106 import SH1106_I2C

i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
display = SH1106_I2C(72, 40, i2c)      # width, height

display.fill(0)
display.text("hello", 0, 0, 1)
display.show()
```

It subclasses `framebuf.FrameBuffer`, so `fill`, `pixel`, `text`, `line`, `rect`, `fill_rect`,
`ellipse`, `blit` and `scroll` all work as they do on any other MicroPython display.

## The ESP32-C3 SuperMini with the 0.42 inch OLED

The display on that board is 72x40 — 0.42 is the diagonal in inches, not a resolution — wired to
I2C at address `0x3C`:

| Display | ESP32-C3 SuperMini |
| --- | --- |
| SCL | GPIO 6 |
| SDA | GPIO 5 |

```python
i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
display = SH1106_I2C(72, 40, i2c)
```

Nothing else needs setting: the offset below is worked out for you.

## The column offset

The SH1106 has **132 columns** of memory while most panels are narrower, so a panel is a window
centred in it. The driver works out where from the width:

| Panel | Offset |
| --- | --- |
| 128 wide | 2 |
| 72 wide | 30 |

Upstream fixes this at 2, which is why a narrow panel drawn by the unmodified driver appears
shifted or clipped. If your panel is not centred in its memory, `x_offset=` overrides it:

```python
display = SH1106_I2C(72, 40, i2c, x_offset=28)
```

Text running off one edge, with a matching blank strip at the other, is this and nothing else.

## Notes

- `rotate=180` turns the picture round for a panel mounted upside down; `rotate=90` and `270`
  work too, at the cost of a second buffer and some speed.
- The driver only sends the pages you have drawn on since the last `show()`, which makes updates
  noticeably quicker on a small panel. `show(full_update=True)` sends all of them.
- Some modules need a reset pin held high. Pass `res=Pin(n)` if yours has one; most I2C modules
  do not.
- If a scan finds nothing at `0x3C`, try `0x3D`, and check the pins: on the C3 boards they are
  not the ones the plain SuperMini uses.

## Tests

`python3 -B drivers/sh1106/test_sh1106.py` checks the commands sent before each page, which is
what decides where the pixels land: the offset for a 128 and a 72 wide panel, that an offset
past 15 sends its high nibble, and that each page is written separately.

## Credits

From [robert-hh/SH1106](https://github.com/robert-hh/SH1106), MIT, Copyright 2016 Radomir
Dopieralski, 2017-2021 Robert Hammelrath and 2021 Tim Weber. Changed for this catalog so the
column offset follows the panel width rather than being fixed at 2.
