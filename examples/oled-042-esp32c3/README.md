---
example: oled-042-esp32c3
author: Steven Slaa
---

# 0.42 inch OLED (ESP32-C3 SuperMini)

Drives the little OLED built into an ESP32-C3 SuperMini. It draws a border to show the geometry
is right, then a clock counting up since boot.

Two things about this display are not what the listing says, and each of them has a distinctive
symptom:

- **It is 72x40 pixels.** The 0.42 is the diagonal in inches.
- **It is an SH1106**, not the SSD1306 these boards are sold as.

## Requires
This example needs the [SH1106 OLED](../../drivers/sh1106) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Nothing to wire — the display is on the board. It is at I2C address `0x3C` on:

| | GPIO |
| --- | --- |
| SCL | 6 |
| SDA | 5 |

These are **not** the pins a plain SuperMini uses, so a pinout found elsewhere will not work.

## Run it

A border round the whole panel with `0.42in` and `72x40` inside it, then:

```
ESP32-C3
SuperMini
up 12s
```

with a line along the bottom that grows a pixel a second. The border is worth keeping while you
set a display like this up: all four edges should sit on the edges of the glass, and any gap or
clipped edge is a geometry problem you can then measure.

## Why it needs a setup sequence

```python
display = SH1106_I2C(72, 40, i2c, setup=PANEL_72X40)
```

The panel powers up with the defaults for a 128x64 screen, and two of them are wrong:

| | Default | This panel |
| --- | --- | --- |
| Multiplex ratio | 64 rows | 40 rows |
| Display offset | 0 | 52 |

The multiplex ratio causes both of the symptoms people report first. Driving 64 rows when only
40 are connected spreads the same brightness over more row-time, so **the display is dim**, and
it maps the panel's rows onto pages the driver never writes, so **the rest is noise**.

The offset is where the panel sits: a 40 row panel is centred in the 64 the controller scans, 12
rows in, which this driver's scan direction asks for as `64 - 12`.

## What the symptoms mean

Worth knowing, because each one points somewhere different:

| What you see | What it is |
| --- | --- |
| Top 8 rows right, everything below noise | An SSD1306 driver on this SH1106. It sends the whole frame in one go, which this controller wraps into page 0 |
| Noise below a correct strip, and dim | The multiplex ratio, still at 64 |
| Picture sits high or low by a fixed amount | The display offset |
| Text upside down or mirrored | `rotate=180`, not an offset |
| Nothing at all | Check `0x3C` appears in an I2C scan on pins 6 and 5 |

## Fitting anything on it

40 pixels is five lines of the built-in 8 pixel font, and 72 is nine characters. Small displays
are mostly an exercise in leaving things out: one number large, or three short lines, and no
labels that can be inferred.

## Tested

The display configuration in this example — 72x40, SH1106, `PANEL_72X40`, pins 6 and 5 — was
measured on an ESP32-C3 SuperMini: a border drawn round the whole buffer lines up with the glass
exactly. The example script itself has not been run end to end yet. If you try it, say so here.
