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

Being pure Python it is slow for full screen redraws; for animation use a C driver instead.

## Credits

Written by Russ Hughes, MIT — <https://github.com/russhughes/st7789py_mpy>, based on devbis'
`st7789py_mpy`.

Used by: [spi-st7789-display](../../examples/spi-st7789-display)
