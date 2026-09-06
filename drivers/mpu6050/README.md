---
driver: mpu6050
---

# MPU-6050

Accelerometer, gyroscope and temperature driver for the MPU-6050 over I2C.

## Install

Install it from the Pulsar IoT library panel, or copy `mpu6050.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
import mpu6050

sensor = mpu6050.accel(SoftI2C(scl=Pin(22), sda=Pin(21)))
print(sensor.get_values())
```

`get_values()` returns raw counts, not g or degrees per second. Divide by the scale of the range
the chip is configured for, and expect a per-chip offset you have to calibrate out while the
sensor is still.

## Credits

This driver came into the repository without a header, a licence or a link, and it matches
several copies of the same code circulating in tutorials. Its origin is therefore unknown and no
author is recorded for it, rather than crediting the wrong person. If you recognise it, say so
and it can be credited properly.

Used by: [i2c-mpu-6050](../../examples/i2c-mpu-6050)
