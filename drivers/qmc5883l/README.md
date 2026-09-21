---
driver: qmc5883l
author: Steven Slaa
---

# QMC5883L magnetometer

## What it is

The QMC5883L is a three axis magnetometer made by QST. It measures the strength of the magnetic
field along X, Y and Z, and because the earth's field points (roughly) north, the ratio between
X and Y gives you a compass heading. It is the chip inside most cheap "digital compass" modules,
including the HW-246 and nearly every GY-271 sold today.

It replaced the Honeywell HMC5883L after Honeywell stopped making that chip, in the same
footprint, but it is not a drop-in replacement: it has a different I2C address, a different
register map and a different byte order. Code written for an HMC5883L reads nothing, or garbage,
from a QMC5883L.

| | |
| --- | --- |
| Measures | magnetic field on three axes, 16 bit |
| Range | ±2 or ±8 gauss (the earth is about 0.25 to 0.65 gauss) |
| Heading accuracy | 1 to 2 degrees, once calibrated and held flat |
| Supply | 2.16V to 3.6V (modules with a regulator also take 5V) |
| Interface | I2C, address `0x0D`, fixed |
| Data rate | 10, 50, 100 or 200 Hz |

Not sure which chip your module has? Run `i2c.scan()`: `0x0D` (13) is a QMC5883L, `0x1E` (30) an
HMC5883L, which has its own [hmc5883l](../hmc5883l) driver.

## Install

Install it from the Pulsar IoT library panel, or copy `qmc5883l.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from qmc5883l import QMC5883L

sensor = QMC5883L(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.magnetic)      # (x, y, z) in microtesla
print(sensor.heading())     # degrees clockwise from magnetic north
print(sensor.overflow)      # True if the field went past the range
```

## Settings

```python
from qmc5883l import QMC5883L, RANGE_2G, RATE_50HZ, OVERSAMPLE_256

sensor = QMC5883L(i2c, field_range=RANGE_2G, rate=RATE_50HZ, oversample=OVERSAMPLE_256)
```

| Setting | Options | Default |
| --- | --- | --- |
| `field_range` | `RANGE_2G` (12 000 counts per gauss), `RANGE_8G` (3 000 counts per gauss) | `RANGE_8G` |
| `rate` | `RATE_10HZ`, `RATE_50HZ`, `RATE_100HZ`, `RATE_200HZ` | `RATE_200HZ` |
| `oversample` | `OVERSAMPLE_512`, `_256`, `_128`, `_64`. More is less noisy and uses more current | `OVERSAMPLE_512` |

`RANGE_2G` gives four times finer steps, which is plenty for a compass. Near a magnet, a speaker
or a motor it overflows sooner: when `overflow` is True the reading is clipped, so switch to
`RANGE_8G`.

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
sensor = QMC5883L(i2c, offset=(4.1, -12.7, 0.9), scale=(1.0, 1.08, 0.97))
```

The correction is only valid where it was taken. Move the module or put a motor next to it, and
it needs doing again.

## Notes

- The heading assumes the board is flat. Tilt it and the reading swings; correcting for that
  needs an accelerometer as well, which this chip does not have.
- `heading(declination=...)` converts magnetic north to true north. In the Netherlands the
  declination is around +2 degrees; look up the value for your location, it drifts over years.
- Register `0x0B` has to be written with `0x01` or the readings drift. The datasheet barely
  mentions it; the driver does it for you.
- The chip has a temperature register, but its offset is not calibrated at the factory and only
  good for measuring change, so the driver does not expose it.
- Some modules carry a QMC5883P at `0x2C` instead. That is another chip with another register
  map, and this driver does not support it.
- Keep it away from the board's antenna and any motor wiring. A few centimetres matters more
  than any amount of software.

## Tests

`python3 -B drivers/qmc5883l/test_qmc5883l.py` checks the control register packing, the scaling
at both ranges and the heading and calibration maths, off-board.

Written from the [QST QMC5883L datasheet](https://datasheet.lcsc.com/lcsc/QST-QMC5883L-TR_C192585.pdf).

Used by: [i2c-compass-qmc5883l](../../examples/i2c-compass-qmc5883l)
