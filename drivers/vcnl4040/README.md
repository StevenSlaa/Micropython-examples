---
driver: vcnl4040
author: Steven Slaa
---

# VCNL4040 proximity and light

Proximity and ambient light driver for the Vishay VCNL4040. It pulses an infrared LED and
measures what comes back, alongside a real lux reading from a separate ambient light channel.

Proximity is a **count, not a distance**. It rises as something approaches — a few hundred at
arm's length, thousands against a hand — and how fast depends on the LED settings and on how
reflective the object is. Use it for "something is near", not for millimetres. If you need a
distance, use the [VL6180X](../vl6180x) instead.

## Install

Install it from the Pulsar IoT library panel, or copy `vcnl4040.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from vcnl4040 import VCNL4040

sensor = VCNL4040(SoftI2C(scl=Pin(22), sda=Pin(21)))

print(sensor.proximity)   # a count that grows as something comes closer
print(sensor.lux)         # ambient light in lux
print(sensor.white)       # the white channel, which also sees infrared
```

Detecting a hand rather than reading a number:

```python
NEAR = 200   # whatever proximity reads with your hand where you want the trigger

while True:
    if sensor.proximity > NEAR:
        print("hand")
    sleep(0.1)
```

## Cancelling cover glass

Mounted behind glass or plastic, the LED reflects straight back into the detector and proximity
sits at a few hundred with nothing in front of it. Read it once with the view clear and hand the
number back:

```python
print(sensor.proximity)     # say it reads 312 with nothing there
sensor.cancellation = 312   # now clear air reads about zero again
```

The value is a property of that particular window, so it needs redoing if the housing changes.

## Notes

- The I2C address is `0x60` and is fixed.
- The driver starts the LED at 200mA with a 1/40 duty cycle, the strongest of the available
  settings, because the defaults in the chip barely reach past the package. Drop
  `led_current=LED_50MA` if the current matters more than the range.
- Proximity is 12 bit by default, so it stops rising at 4095 when something is very close. Pass
  `high_resolution=True` for the 16 bit output.
- `lux` is scaled for the integration time in use. Longer integration sees dimmer light at the
  cost of speed: `sensor.integration_time = ALS_640MS` is eight times as sensitive as the 80ms
  default and takes eight times as long.
- `light` is the raw count behind `lux`, useful only if you are doing the scaling yourself.
- `white` responds to infrared as well as visible light, so it reads high under an incandescent
  bulb or in sunlight where `lux` does not. Comparing the two is how these sensors tell daylight
  from a lamp.
- Sunlight falling directly on the sensor swamps the LED, and proximity stops responding. That
  is the part, not the driver.

## Tests

`python3 -B drivers/vcnl4040/test_vcnl4040.py` checks the register packing, the lux scaling and
the settings that share a register, off-board.

Used by: [i2c-proximity-vcnl4040](../../examples/i2c-proximity-vcnl4040)
