---
driver: st7789py
author: Russ Hughes
---

# ST7789 display

Pure MicroPython driver for ST7789 SPI colour displays (240x240 and 240x320), plus the
`vga2_16x32.py` bitmap font used by the example.

## Install

Install it from the Pulsar IoT library panel, or copy `st7789py.py` and `vga2_16x32.py`
to `/lib` on the board.

## Usage

```python
from machine import Pin, SPI
import st7789py as st7789
import vga2_16x32 as font

spi = SPI(1, baudrate=30000000, sck=Pin(18), mosi=Pin(19))
display = st7789.ST7789(spi, 240, 240, reset=Pin(23, Pin.OUT), dc=Pin(16, Pin.OUT))
display.text(font, "Hello", 0, 0)
```

## Speed

Measured on a TTGO T-Display v1.1 (ESP32 at 240MHz, 135x240 panel). The bus runs at 26.67MHz
there, because MOSI is not one of the ESP32's direct SPI pins and the signals go through the GPIO
matrix:

| | |
| --- | ---: |
| Full screen fill | 26 ms (38 fps) |
| Text, 15 characters of 16x32 | 46 ms, 157 ms the first time |
| Blit 60x60 pixels | 4.0 ms |
| Horizontal line, 240 pixels | 3.4 ms |

Characters are built through a lookup table and then kept, so redrawing the same text in the same
colours costs no more than sending it. The cache holds 16 characters and four colour pairs; beyond
that it is emptied and refilled. Filling reuses one buffer rather than allocating a new one per
call, which on a board with a busy heap is the difference between working and a `MemoryError`.

`pixel()` costs about 2.7 ms whatever it draws, because every pixel sets a drawing window. Use
`fill_rect()` or `blit_buffer()` instead of drawing pixel by pixel.

Being pure Python it remains too slow for full screen animation; for that use a C driver, or an
8-bit parallel display like the [st7789-parallel](../st7789-parallel) one.

## Credits

Written by Russ Hughes, MIT — <https://github.com/russhughes/st7789py_mpy>, based on devbis'
`st7789py_mpy`.

Used by: [spi-st7789-display](../../examples/spi-st7789-display)
