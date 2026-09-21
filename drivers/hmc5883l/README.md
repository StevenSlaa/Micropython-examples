---
driver: hmc5883l
author: Steven Slaa
---

# HMC5883L magnetometer

## What it is

The HMC5883L is a three axis magnetometer made by Honeywell. It measures the strength of the
magnetic field along X, Y and Z, and because the earth's field points (roughly) north, the ratio
between X and Y gives you a compass heading. It was the chip on the original GY-271 modules.

Honeywell has stopped making it, and most modules sold as GY-271 today carry the QST QMC5883L
instead. The two share a footprint and nothing else: a different I2C address, a different
register map and a different byte order. Use the [qmc5883l](../qmc5883l) driver for that one.

| | |
| --- | --- |
| Measures | magnetic field on three axes, 12 bit |
| Range | ±0.88 to ±8.1 gauss (the earth is about 0.25 to 0.65 gauss) |
| Heading accuracy | 1 to 2 degrees, once calibrated and held flat |
| Supply | 2.16V to 3.6V (modules with a regulator also take 5V) |
| Interface | I2C, address `0x1E`, fixed |
| Data rate | 0.75 to 75 Hz |

Not sure which chip your module has? Run `i2c.scan()`: `0x1E` (30) is an HMC5883L, `0x0D` (13) a
QMC5883L.

## Install

Install it from the Pulsar IoT library panel, or copy `hmc5883l.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from hmc5883l import HMC5883L

sensor = HMC5883L(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.magnetic)      # (x, y, z) in microtesla
print(sensor.heading())     # degrees clockwise from magnetic north
print(sensor.overflow)      # True if the last reading went past the range
```

## Settings

```python
from hmc5883l import HMC5883L, RANGE_4G, RATE_75HZ, AVERAGE_1

sensor = HMC5883L(i2c, field_range=RANGE_4G, rate=RATE_75HZ, average=AVERAGE_1)
```

| Setting | Options | Default |
| --- | --- | --- |
| `field_range` | `RANGE_0_88G`, `_1_3G`, `_1_9G`, `_2_5G`, `_4G`, `_4_7G`, `_5_6G`, `_8_1G` (1370 down to 230 counts per gauss) | `RANGE_1_3G` |
| `rate` | `RATE_0_75HZ`, `_1_5HZ`, `_3HZ`, `_7_5HZ`, `_15HZ`, `_30HZ`, `_75HZ` | `RATE_15HZ` |
| `average` | `AVERAGE_1`, `_2`, `_4`, `_8` samples per reading. More is less noisy | `AVERAGE_8` |

`RANGE_1_3G` is plenty for a compass. Near a magnet, a speaker or a motor it overflows: the chip
then reports -4096 on the clipped axis, the driver sets `overflow`, and you should pick a wider
range.

## Calibrating

An uncalibrated compass can be tens of degrees out, because it reads the magnet in a nearby
speaker and the steel in your desk as well as the earth. Turn the module slowly through every
orientation, including upside down, while `calibrate()` runs:

```python
offset, scale = sensor.calibrate(seconds=20)
print(offset, scale)        # keep these
```

Then skip the ritual next time:

```python
sensor = HMC5883L(i2c, offset=(4.1, -12.7, 0.9), scale=(1.0, 1.08, 0.97))
```

The correction is only valid where it was taken. Move the module or put a motor next to it, and
it needs doing again.

## Notes

- The heading assumes the board is flat. Tilt it and the reading swings; correcting for that
  needs an accelerometer as well, which this chip does not have.
- `heading(declination=...)` converts magnetic north to true north. In the Netherlands the
  declination is around +2 degrees; look up the value for your location, it drifts over years.
- The data registers run X, **Z**, Y, not X, Y, Z. The driver reorders them for you.
- Keep it away from the board's antenna and any motor wiring. A few centimetres matters more
  than any amount of software.

## Tests

`python3 -B drivers/hmc5883l/test_hmc5883l.py` checks the configuration registers, the axis order,
the scaling, overflow and the heading and calibration maths, off-board.

Written from the [Honeywell HMC5883L datasheet](https://cdn-shop.adafruit.com/datasheets/HMC5883L_3-Axis_Digital_Compass_IC.pdf).

Used by: [i2c-compass-hmc5883l](../../examples/i2c-compass-hmc5883l)
