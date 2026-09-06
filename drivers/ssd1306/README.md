---
driver: ssd1306
author: micropython-lib contributors
---

# SSD1306 OLED

Monochrome SSD1306 OLED driver for the common 128x64 and 128x32 modules, over I2C or SPI.
`SSD1306` subclasses `framebuf.FrameBuffer`, so every drawing primitive of
[`framebuf`](https://docs.micropython.org/en/latest/library/framebuf.html) works: `text`, `pixel`,
`line`, `rect`, `fill_rect`, `blit`, `scroll`.

## Install

Install it from the Pulsar IoT library panel, or copy `ssd1306.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
display = SSD1306_I2C(128, 64, i2c)

display.fill(0)
display.text("Hello", 0, 0)
display.show()          # nothing appears until show()
```

Over SPI:

```python
from machine import Pin, SPI
from ssd1306 import SSD1306_SPI

display = SSD1306_SPI(128, 64, SPI(1), dc=Pin(16), res=Pin(17), cs=Pin(5))
```

## Notes

- Set the size to match the panel: `SSD1306_I2C(128, 32, i2c)` for the short modules. A wrong
  height gives a squashed or repeated image.
- The I2C address is `0x3C` on most modules and `0x3D` on a few; pass `addr=0x3D` if the display
  stays blank. Run the [i2c-scanner](../../examples/i2c-scanner) example to find out which.
- Drawing only changes the in-memory buffer. Call `show()` to push it to the panel.
- Modules with their own charge pump are the default; pass `external_vcc=True` only if the board
  is wired for an external display supply.
- `contrast(0..255)` dims the panel, `invert(1)` swaps black and white, `rotate(0|1)` flips it
  180° for upside-down mounting.

## Credits

From [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display/ssd1306), MIT.
