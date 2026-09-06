---
driver: i2c-lcd
author: Dave Hylands
---

# I2C character LCD

HD44780 character LCD driver for displays behind a PCF8574 I2C backpack (the common 16x2 and
20x4 modules). `lcd_api.py` holds the display commands, `i2c_lcd.py` talks to the backpack.

## Install

Install it from the Pulsar IoT library panel, or copy both files to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from i2c_lcd import I2cLcd

lcd = I2cLcd(SoftI2C(scl=Pin(22), sda=Pin(21)), 0x27, 2, 16)
lcd.putstr("Hello")
```

Backpacks ship with different I2C addresses; run the [i2c-scanner](../../examples/i2c-scanner)
example if `0x27` does not respond.

## Credits

Based on Dave Hylands' `python_lcd` — <https://github.com/dhylands/python_lcd>.

Used by: [i2c-liquid-crystal-display](../../examples/i2c-liquid-crystal-display)
