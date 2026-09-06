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

## OSError: [Errno 19] ENODEV

The sensor is not acknowledging its address on the bus at all, so nothing can be read from it.

**Power cycle it.** Unplug and replug the board; a soft reset leaves the sensor powered and it
will not recover. An I2C scan finding nothing at `0x29` afterwards means it is wiring or power,
not software.

The usual way to get a VL6180X into this state is writing ST's private tuning registers to a
sensor that is already running, which is why the driver only writes them to one that has just
powered up, or one whose readback shows it never got them. `reconfigure()` writes them
deliberately, and carries the same warning.

## Nothing but errors

Every reading coming back as *early convergence estimate failed* (status 6) or *signal to noise
too low* (status 11) means the sensor is working and talking, but no usable light is coming
back. In order of how often it turns out to be the cause:

1. **The protective film is still on the sensor.** These modules ship with a small clear sticker
   over the two windows. It passes visible light, so it looks like nothing is there.
2. **The target is too far.** This part reaches about 10cm, up to 20cm against white matt card.
   A wall across the room reads as an error, not as a large number. Test with a sheet of paper
   at 5cm before anything else.
3. **The target is dark, shiny, or at an angle.** Matt black absorbs the pulse and glass or
   polished metal reflects it away from the sensor. Try white paper held square on.
4. **Something is over the windows.** Cover glass, a printed bezel, or hot glue across the
   emitter scatters the pulse straight back into the detector and ruins short readings.
5. **Give it longer to gather light**, which helps a dark or distant target:

   ```python
   sensor.convergence_time = 63   # milliseconds, 49 by default, 63 is the maximum
   ```

To confirm the sensor is configured rather than just wired, read back a register the start-up
sequence sets:

```python
print(hex(sensor._read(0x003F)))   # 0x46 once the tuning has been written
print(hex(sensor._read(0x010A)))   # 0x30
```

## Notes

- The I2C address is `0x29` and cannot be strapped. Two of them on one bus means changing one
  in software at start-up while the other is held in reset by its CE pin.
- The sensor uses 16 bit register addresses, unlike most I2C parts. The driver passes
  `addrsize=16` for you, but that is why a generic register tool shows nothing useful.
- ST's start-up tuning is written when the sensor's own fresh-out-of-reset flag is set, and
  also when a register the sequence sets reads back wrong — which catches a powered but untuned
  sensor, the case the flag alone misses after the board reboots over USB. It is deliberately
  not written on every construction: those are private registers, and a running sensor can stop
  answering on the bus entirely.
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

Used by: [i2c-tof-vl6180x](../../examples/i2c-tof-vl6180x)
