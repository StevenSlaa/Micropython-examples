# VL6180X range and light

Time of flight distance and ambient light driver for the ST VL6180X. It times a pulse of
infrared light rather than guessing from brightness, so the reading barely cares what colour
the target is — but the range is short: about 10cm reliably, up to 20cm against something
white and matt.

## Install

Install it from the Pulsar IoT library panel, or copy `vl6180x.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from vl6180x import VL6180X, GAIN_1

sensor = VL6180X(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.range, "mm")
print(sensor.lux(GAIN_1), "lux")
```

Every reading is a fresh single measurement, and each one blocks for a few milliseconds while
the sensor works.

## Checking a reading

`range` returns a number whatever happens; `range_status` says whether to believe it:

```python
from vl6180x import RANGE_ERRORS

distance = sensor.range
if sensor.range_status == 0:
    print(distance, "mm")
else:
    print("bad reading:", RANGE_ERRORS.get(sensor.range_status, "unknown"))
```

With nothing in front of the sensor the status is 7 (*no convergence*) and the distance is
meaningless, so a program that ignores the status reads empty air as a number.

## Notes

- The I2C address is `0x29` and cannot be strapped. Two of them on one bus means changing one
  in software at start-up while the other is held in reset by its CE pin.
- The sensor uses 16 bit register addresses, unlike most I2C parts. The driver passes
  `addrsize=16` for you, but that is why a generic register tool shows nothing useful.
- ST's start-up tuning is written on the first power-up only, which is what the sensor's own
  fresh-out-of-reset flag is for. Skipping it gives a sensor that reads, but badly.
- Range accuracy is a few millimetres and varies part to part. `VL6180X(i2c, offset=-3)` trims
  the reading in software; `sensor.part_to_part_offset` writes the sensor's own offset register
  instead, which survives into other drivers but not a power cycle.
- Cover glass in front of the sensor reflects some of the light straight back and ruins the
  short readings. The datasheet asks for an air gap and a mask; in practice, keep the window
  clear of the emitter.
- `lux()` assumes the 100ms integration time the driver sets. A brightly lit room reads a few
  hundred lux at `GAIN_1`; use a higher gain indoors at night, a lower one in daylight.
- A sensor that never answers raises `OSError` after `timeout` milliseconds (500 by default)
  rather than blocking the board forever.

## Tests

`python3 -B drivers/vl6180x/test_vl6180x.py` checks the start-up sequence, the register
handling, the lux and offset maths, and the timeout, off-board.
