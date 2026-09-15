---
driver: bmm150
author: Steven Slaa
---

# BMM150 magnetometer

## What it is

The BMM150 is a three axis geomagnetic sensor made by Bosch Sensortec: a magnetometer built to
measure the earth's magnetic field, and so to work as a compass. It measures the field along X, Y
and Z, and with the sensor held flat the ratio between X and Y gives a heading.

It is tiny (1.56 × 1.56mm) and frugal, which is why it turns up in phones, wearables and boards
like the Arduino Nano 33 BLE Sense Rev2, as well as on breakouts such as the M5Stack BMM150 unit,
the DFRobot Gravity BMM150 and the GY-BMM150.

| | |
| --- | --- |
| Measures | magnetic field on three axes |
| Range | ±1300µT on X and Y, ±2500µT on Z (the earth is about 25 to 65µT) |
| Resolution | about 0.3µT |
| Supply | 1.62V to 3.6V |
| Interface | I2C, address `0x10` to `0x13`, set by the CS and SDO pins |
| Data rate | 2 to 30Hz |

Compared with the [QMC5883L](../qmc5883l) it is smaller and uses less power, but it is more work
to read: its raw counts are not a field strength. Every chip is trimmed at the factory, and each
reading has to go through Bosch's compensation with those trim values and a resistance the chip
measures alongside every sample. The driver does all of that; you get microtesla.

## Install

Install it from the Pulsar IoT library panel, or copy `bmm150.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from bmm150 import BMM150

sensor = BMM150(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.magnetic)      # (x, y, z) in microtesla
print(sensor.heading())     # degrees clockwise from magnetic north
```

If it says `No BMM150 at 0x10`, run `i2c.scan()` and pass the address it finds, for example
`BMM150(i2c, address=0x13)`. Several breakouts ship at `0x13`.

## Troubleshooting

| Message | Means |
| --- | --- |
| `No BMM150 at 0x13` | nothing acknowledged that address. Check the address with `i2c.scan()` and the wiring |
| `0x13 answered, but gave no chip id after power on` | the chip is there but would not answer a read. Try a slower bus (`freq=10000`), shorter wires, or pull-up resistors if the breakout has none |
| `0x13 is not a BMM150 (chip id 0x00)` | the chip did not wake up, or another part shares the address |

On a Raspberry Pi Pico with `SoftI2C`, the very first transaction on a newly created bus is
refused with `ENODEV`, every time, and the next one works. Hardware `I2C(0)` or `I2C(1)` does not
do this. The driver retries, so it only matters when you talk to the chip yourself: start with an
`i2c.scan()`, as below.

The same check by hand, in the REPL:

```python
from time import sleep_ms
i2c.scan()                                         # absorbs the refused first transaction
i2c.writeto_mem(0x13, 0x4B, b"\x01")               # wake it up
sleep_ms(10)
print(hex(i2c.readfrom_mem(0x13, 0x40, 1)[0]))     # a BMM150 prints 0x32
```

## Settings

```python
from bmm150 import BMM150, HIGH_ACCURACY, RATE_20HZ

sensor = BMM150(i2c, preset=HIGH_ACCURACY, rate=RATE_20HZ)
```

`preset` picks how many measurements the chip averages into each sample. These are Bosch's four
presets:

| Preset | Noise | Current | Rate |
| --- | --- | --- | --- |
| `LOW_POWER` | 1.0µT | 0.17mA | up to 30Hz |
| `REGULAR` (default) | 0.6µT | 0.5mA | up to 30Hz |
| `ENHANCED` | 0.5µT | 0.8mA | up to 30Hz |
| `HIGH_ACCURACY` | 0.3µT | 4.9mA | up to 20Hz |

`rate` is one of `RATE_2HZ`, `RATE_6HZ`, `RATE_8HZ`, `RATE_10HZ` (default), `RATE_15HZ`,
`RATE_20HZ`, `RATE_25HZ` and `RATE_30HZ`. `HIGH_ACCURACY` takes too long per sample to go faster
than 20Hz; ask for more and you simply get fewer fresh samples.

## Calibrating

An uncalibrated compass can be tens of degrees out, because it reads the magnet in a nearby
speaker and the steel in your desk as well as the earth. The factory trim does not fix that: it
corrects the chip, not its surroundings. Turn the module slowly through every orientation,
including upside down, while `calibrate()` runs:

```python
offset, scale = sensor.calibrate(seconds=20)
print(offset, scale)        # keep these
```

Then skip the ritual next time:

```python
sensor = BMM150(i2c, offset=(4.1, -12.7, 0.9), scale=(1.0, 1.08, 0.97))
```

The correction is only valid where it was taken. Move the module or put a motor next to it, and
it needs doing again.

## Notes

- **An axis that overflows reads `nan`**, not a number. That happens next to a strong magnet, and
  for the very first reading after start-up, before the chip has taken a sample: wait one
  sample (100ms at 10Hz) before reading. `value == value` is False only for `nan`, if you need
  to test for it.
- The heading assumes the board is flat. Tilt it and the reading swings; correcting for that
  needs an accelerometer as well.
- `heading(declination=...)` converts magnetic north to true north. Look up the value for your
  location; it drifts over years.
- Which way is X depends on how the chip sits on your breakout. If the heading runs backwards or
  is 90 degrees off, check the axis markings on the board.
- `0x10` is also the address of a VEML7700 light sensor. On a shared bus, the driver checks the
  chip id and says so if it finds something that is not a BMM150.
- The chip has no temperature output. The resistance it measures with each sample is used to
  correct the reading for temperature, but it is not a temperature in any unit.
- Forced mode, interrupts and the self test are not used.

## Tests

`python3 -B drivers/bmm150/test_bmm150.py` checks the power up order, the bit unpacking, the trim
compensation against values worked out by hand, overflow handling and the heading and
calibration maths, off-board.

Written from the [Bosch BMM150 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmm150-ds001.pdf),
with the compensation ported from Bosch's
[BMM150 Sensor API](https://github.com/boschsensortec/BMM150_SensorAPI) (BSD-3-Clause).

Used by: [i2c-compass-bmm150](../../examples/i2c-compass-bmm150)
