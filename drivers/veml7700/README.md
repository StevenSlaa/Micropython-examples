---
driver: veml7700
author: Steven Slaa
---

# VEML7700 ambient light

Ambient light driver for the Vishay VEML7700. It reads light in lux through a filter matched
to the human eye, plus a white channel that also sees infrared. With the right settings it
covers everything from a dark room to about 140 000 lux, but no single setting covers all of it.

## Install

Install it from the Pulsar IoT library panel, or copy `veml7700.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from veml7700 import VEML7700

sensor = VEML7700(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.lux)     # ambient light in lux
print(sensor.white)   # the white channel, which also sees infrared
print(sensor.light)   # the raw count behind lux
```

## Picking a range

Gain and integration time trade range against fine steps. Lower gain and shorter integration
time reach brighter light with coarser steps:

| Setting | Lux per count | Saturates at |
| --- | --- | --- |
| `GAIN_2`, `IT_800MS` | 0.0042 | 275 lux |
| `GAIN_1`, `IT_100MS` | 0.067 | 4 400 lux |
| `GAIN_1_4`, `IT_100MS` (default) | 0.27 | 17 600 lux |
| `GAIN_1_8`, `IT_25MS` | 2.15 | 140 900 lux |

```python
from veml7700 import VEML7700, GAIN_1_8, IT_25MS

sensor = VEML7700(i2c, gain=GAIN_1_8, integration_time=IT_25MS)   # outdoors
sensor.gain = GAIN_2                                               # or change it later
```

A `light` of 65535 means the sensor is saturated and `lux` is too low. Pick a less sensitive
setting. The driver does not switch range on its own.

## Notes

- The I2C address is `0x10` and is fixed.
- The chip powers up shut down. The driver turns it on, and a fresh reading arrives one
  integration time later. Read sooner and you get an empty or stale value, because the chip
  keeps its last reading through a shutdown. The same wait applies after changing a setting.
- `lux` is linear in the raw count. Older Vishay application notes add a polynomial
  correction for bright light, but it runs away above about 20 000 lux, so the driver leaves
  it out.
- Vishay's current datasheet gives 0.0042 lux per count at gain 2 and 800ms, and older ones
  0.0036. Pass `resolution=` to change it, or to calibrate against a light meter you trust.
- `white` responds to infrared as well as visible light, so it reads high next to `lux` under
  an incandescent bulb or in sunlight. Comparing the two is how to tell daylight from an LED
  lamp.
- Interrupts and power saving mode are not used.

## Tests

`python3 -B drivers/veml7700/test_veml7700.py` checks the register packing and the lux scaling
at each end of the range, off-board.

Written from the [Vishay VEML7700 datasheet](https://www.vishay.com/docs/84286/veml7700.pdf).

Used by: [i2c-light-veml7700](../../examples/i2c-light-veml7700)
