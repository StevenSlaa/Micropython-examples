# BMP280

Temperature and pressure driver for the Bosch BMP280 over I2C or SPI.

## Install

Install it from the Pulsar IoT library panel, or copy `bmp280.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from bmp280 import BMP280

bmp = BMP280(SoftI2C(scl=Pin(22), sda=Pin(21)))
print(bmp.temperature, bmp.pressure)
```

## Credits

Written by David Stenwall — <https://github.com/dafvid/micropython-bmp280>.

Used by: [i2c-bmp280](../../examples/i2c-bmp280)
