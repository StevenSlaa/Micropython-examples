---
driver: st7789-parallel
author: Steven Slaa
---

# ST7789 8-bit parallel display

Pure MicroPython driver for ST7789 colour LCDs connected through an Intel 8080-style 8-bit
parallel bus. Its defaults are the 170x320 panel in the 1.9 inch LilyGO/TTGO T-Display-S3.

This is not the same interface as an SPI ST7789 module. Use the existing
[st7789py](../st7789py) driver for those.

## Install

Install it from the Pulsar IoT library panel, or copy `st7789_parallel.py` to `/lib` on the
board together with `rgb565_display.py` from the [rgb565-display](../rgb565-display) driver, which
holds the drawing methods it shares with other colour displays.

## Usage

The driver keeps pin numbers out of the reusable module. This is the wiring already built into
the T-Display-S3:

```python
from machine import Pin
from st7789_parallel import ST7789Parallel, BLACK, WHITE

Pin(15, Pin.OUT, value=1)  # peripheral power; do this before constructing the display

display = ST7789Parallel(
    [Pin(pin, Pin.OUT) for pin in (39, 40, 41, 42, 45, 46, 47, 48)],  # D0..D7
    wr=Pin(8, Pin.OUT),
    dc=Pin(7, Pin.OUT),
    cs=Pin(6, Pin.OUT),
    reset=Pin(5, Pin.OUT),
    rd=Pin(9, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    fast=True,
)

display.fill(BLACK)
display.text("Hello!", 10, 10, WHITE, BLACK)
```

Rotation 0 and 2 are 170x320 portrait. Rotation 1 and 3 are 320x170 landscape. The driver draws
straight to the LCD and provides `pixel`, `line`, `hline`, `vline`, `rect`, `fill_rect`, `fill`,
`text`, `bitmap` and `blit_buffer`. Buffers passed to `blit_buffer` are RGB565 with the high byte
first. `bitmap` draws a 1 bit `MONO_HLSB` image, such as a logo, in a colour on a background colour.

## T-Display-S3 pin map

| Signal | GPIO |
| --- | ---: |
| Peripheral power | 15 |
| Backlight | 38 |
| D0, D1, D2, D3 | 39, 40, 41, 42 |
| D4, D5, D6, D7 | 45, 46, 47, 48 |
| Reset | 5 |
| Chip select | 6 |
| Data/command | 7 |
| Write | 8 |
| Read | 9 |

GPIO 15 is easy to miss: it must be high before the display is initialized, particularly when
the board is powered from its battery or header instead of USB.

## Fast mode and memory

`fast=True` selects the T-Display-S3 accelerated path. Viper-compiled native loops write the
ESP32-S3 GPIO registers directly: each byte is one data-register write plus a GPIO 8 pulse, and
each command (DC, command byte, parameters) is a single native call. Solid fills repeat the colour
without a pixel buffer, and colours whose two bytes match (black, white) only pulse WR. `text`
renders through `framebuf`'s RGB565 mode instead of a per-pixel Python loop.

Measured on a T-Display-S3 with MicroPython 1.29: a full 320x170 fill takes about 21 ms, a
100x100 blit 10 ms and a 17-character text line 3 ms.

The module uses `@micropython.viper`, so it needs firmware with the native emitter; every
ESP32-S3 build has it. Chip select is held low after initialization, because nothing else shares
the display bus.

Fast mode is tied to the fixed T-Display-S3 pins in the table above. Leave it off if another
ST7789 parallel panel uses different pins; the portable pin-by-pin fallback remains available.

Neither mode reserves a 108,800-byte full-screen framebuffer. Drawing goes straight to the panel,
and solid fills allocate only a small fixed chunk in portable mode.

`text` uses the built-in 8x8 `framebuf` font, so it needs no separate font file. The ST7789 panel
is updated immediately; there is no `show()` call.

The BGR flag in the rotation command is intentional. On the tested T-Display-S3 glass, omitting it
makes red appear blue, yellow cyan, cyan yellow and blue red.

## Credits

The pin map and recommended ST7789 initialization are from LilyGO's
[T-Display-S3 repository](https://github.com/Xinyuan-LilyGO/T-Display-S3) and its bundled
[TFT_eSPI setup](https://github.com/Xinyuan-LilyGO/T-Display-S3/blob/main/lib/TFT_eSPI/User_Setups/Setup206_LilyGo_T_Display_S3.h).
The API and rotation approach were informed by Russ Hughes' MIT-licensed
[T-Display-S3 MicroPython driver](https://github.com/russhughes/t-display-s3).
