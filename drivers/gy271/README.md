---
driver: gy271
author: Steven Slaa
---

# GY-271 compass (QMC5883L / HMC5883L)

Three axis magnetometer driver for the GY-271 and HW-246 modules. Boards sold under both names
carry one of two chips that share a footprint and nothing else, so the driver works out which
one is in front of you and handles the differences.

| | QMC5883L | HMC5883L |
| --- | --- | --- |
| I2C address | `0x0D` | `0x1E` |
| Byte order | little endian | big endian |
| Register order | X, Y, Z | X, **Z, Y** |
| Usually labelled | HW-246, newer GY-271 | older GY-271 |

## Install

Install it from the Pulsar IoT library panel, or copy `gy271.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from gy271 import compass

sensor = compass(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.magnetic)      # (x, y, z) in microtesla
print(sensor.heading())     # degrees clockwise from magnetic north
```

`compass()` picks the chip off the bus. Name one directly if you would rather not scan:

```python
from gy271 import QMC5883L
sensor = QMC5883L(i2c)
```

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
sensor = compass(i2c, offset=(4.1, -12.7, 0.9), scale=(1.0, 1.08, 0.97))
```

The correction is only valid where it was taken. Move the module to a different mounting, or
put a motor next to it, and it needs doing again.

## Notes

- The heading assumes the board is flat. Tilt it and the reading swings; correcting for that
  needs an accelerometer as well, which this module does not have.
- `heading(declination=...)` converts magnetic north to true north. The value for your location
  is a lookup, and it drifts over years.
- Ranges are fixed by the driver: ±8 gauss for the QMC5883L, ±1.3 gauss for the HMC5883L. Both
  are far beyond the earth's roughly 0.5 gauss, so a reading that pins at the limit is a magnet,
  not a bug.
- The QMC5883L has a temperature register, but its offset is uncalibrated at the factory and
  only good for measuring change, so the driver does not expose it.
- Keep it away from the board's own antenna and any motor wiring. A few centimetres matters more
  than any amount of software.

## Tests

`python3 -B drivers/gy271/test_gy271.py` checks the two register maps and the heading and
calibration maths off-board.

Used by: [i2c-compass-gy271](../../examples/i2c-compass-gy271)
