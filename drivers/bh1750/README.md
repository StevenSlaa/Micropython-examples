---
driver: bh1750
author: Steven Slaa
---

# BH1750 ambient light (GY-30)

## What it is

The BH1750 (full name BH1750FVI) is a digital ambient light sensor made by ROHM. It measures how
bright it is and hands you the answer almost directly in lux, the unit for light as the human
eye sees it: its filter follows the eye's sensitivity, and it barely responds to infrared. That
makes it the usual choice for "is it dark yet?", automatic screen brightness, or switching on a
lamp at dusk.

The chip itself is tiny, so it is almost always sold on a module. The **GY-30** (and the round
**GY-302**) put the BH1750 on a small board with a 3.3V regulator and the I2C pull-up resistors,
so you only need four wires.

| | |
| --- | --- |
| Measures | ambient light, 1 to 65 535 lux by default, up to about 120 000 lux |
| Resolution | 4, 1 or 0.5 lux per step, depending on the mode |
| Spectral response | close to the human eye, little infrared |
| Supply | chip 2.4V to 3.6V; GY-30 module 3.3V to 5V |
| Interface | I2C, address `0x23` (ADDR low or open) or `0x5C` (ADDR high) |
| Measurement time | 120ms in high resolution, 16ms in low resolution |

For comparison, the [VEML7700](../veml7700) covers a similar range and adds a white channel
that also sees infrared; the BH1750 is the cheaper, simpler one.

## Install

Install it from the Pulsar IoT library panel, or copy `bh1750.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from bh1750 import BH1750

sensor = BH1750(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.lux)     # ambient light in lux
print(sensor.light)   # the raw count behind it; 65535 means saturated
```

## Settings

```python
from bh1750 import BH1750, CONTINUOUS_HIGH_2

sensor = BH1750(i2c, mode=CONTINUOUS_HIGH_2, mtreg=254)   # very dim light
```

| Mode | Steps | Time per reading |
| --- | --- | --- |
| `CONTINUOUS_HIGH` (default) | 1 lux | 120ms |
| `CONTINUOUS_HIGH_2` | 0.5 lux | 120ms |
| `CONTINUOUS_LOW` | 4 lux | 16ms |

`mtreg`, the measurement time register, runs from 31 to 254 with 69 as the default. It stretches
or shortens the measurement: 254 is 3.7 times more sensitive and slower, down to about 0.11 lux
per step in `CONTINUOUS_HIGH_2`, while 31 reaches about 120 000 lux, enough for direct sunlight.
The time per reading scales with it, so at 254 a reading takes up to about 660ms.

## Notes

- A fresh reading arrives one measurement time after the driver starts the sensor. Read sooner
  and you get 0.
- A `light` of 65535 means the sensor is saturated and `lux` is too low. Use a lower `mtreg`.
  The driver does not switch range on its own.
- The datasheet's 1.2 counts per lux is typical, but a given chip is anywhere from 0.96 to 1.44,
  so readings can be up to 20% off. Pass `accuracy=` to calibrate against a light meter you trust.
- The ADDR pin on a GY-30 is pulled low on the board, so leave it open for `0x23`. Tie it to VCC
  and pass `address=BH1750_ADDRESS_HIGH` to put two sensors on one bus.
- The module accepts 5V, but wire VCC to 3V3 anyway so the I2C pull-ups do not pull the data
  lines of a 3.3V board up to 5V.
- One-shot modes, which power the chip down between readings, are not used.

## Tests

`python3 -B drivers/bh1750/test_bh1750.py` checks the command bytes and the lux scaling across
modes and measurement times, off-board.

Written from the [ROHM BH1750FVI datasheet](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf).

Used by: [i2c-light-bh1750](../../examples/i2c-light-bh1750)
