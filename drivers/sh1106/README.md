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
from sh1106 import SH1106_I2C, PANEL_72X40

i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
display = SH1106_I2C(72, 40, i2c, setup=PANEL_72X40)
```

`PANEL_72X40` matters as much as the size does. These panels power up with the defaults for a
128x64 screen, and two of them are wrong:

| | Default | A 72x40 panel needs |
| --- | --- | --- |
| Multiplex ratio | 64 rows | **40 rows** |
| Display offset | 0 | **52** |

**The multiplex ratio** explains two symptoms at once. Left at 64, the panel drives 24 rows that
are not connected: the same brightness is spread over 64 row-times instead of 40, so it is dim,
and its rows land on pages this driver never writes, so the rest of the glass shows whatever it
powered up with.

**The display offset** is where the panel sits. A short panel is centred in the 64 rows the
controller scans, exactly as a narrow one is centred in its 132 columns — 12 rows in, for a 40
row panel. This driver leaves the scan direction at its default, where the offset counts the
other way round, so those 12 rows are asked for as `64 - 12 = 52`. Both numbers come from the
height, and both reduce to nothing on a full height panel.

What `panel_setup` deliberately does **not** set is the segment remap and the scan direction.
`flip()` runs after it and would undo them. If your picture is upside down or mirrored, use
`rotate=180`, not a setup sequence.

If a panel of yours is not centred, measure it rather than guessing: draw a border round the
whole buffer, step `0xD3` through its 64 values, and use the one where the border lines up with
the glass.

```python
display = SH1106_I2C(72, 40, i2c, setup=panel_setup(40, offset=48))
```

If the picture is then correct but **dim**, the panel wants its charge pump or internal
reference set, and those two commands differ between the controllers:

```python
display.write_cmd(0xAD); display.write_cmd(0x8B)   # SH1106: DC-DC on
display.write_cmd(0x8D); display.write_cmd(0x14)   # SSD1306: charge pump on
```

Send one, not both, and keep whichever brightens it.

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

Used by: [oled-042-esp32c3](../../examples/oled-042-esp32c3)

## Credits

From [robert-hh/SH1106](https://github.com/robert-hh/SH1106), MIT, Copyright 2016 Radomir
Dopieralski, 2017-2021 Robert Hammelrath and 2021 Tim Weber. Changed for this catalog so the
column offset follows the panel width rather than being fixed at 2.
