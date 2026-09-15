---
example: i2c-light-veml7700
author: Steven Slaa
---

# VEML7700 Light Sensor Example

In this example the microcontroller reads a VEML7700 twice a second and prints how bright it is
in lux, along with the white channel, which also sees infrared.

## Requires
This example needs the [VEML7700 ambient light](../../drivers/veml7700) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The sensor sits at I2C address `0x10`, which is fixed. The chip itself only takes 2.5V to 3.6V,
so wire VIN to 3V3. Some breakouts add a regulator and accept 5V, but not all of them do.

| VEML7700 | ESP32 | Pico |
| --- | --- | --- |
| VIN | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

## Output
```
Light:    319.9 lux  White:  1532
Light:    319.1 lux  White:  1529
Light:    108.1 lux  White:   517
Light:      8.3 lux  White:    40
Light:  17615.8 lux  White: 65535  <- saturated
```

## Tuning it

If it says `<- saturated`, the light is too bright for the setting and the lux reading is too
low. Set `gain` to `GAIN_1_8` and `integration_time` to `IT_25MS` at the top of the script. If a
dark room only reads a few lux in coarse steps, go the other way with `GAIN_2` and `IT_800MS`.
The [driver README](../../drivers/veml7700) has the full table.

## Plotter

Open the **Plotter** tab beside the REPL to graph light against the white channel. Cover the
sensor and both fall together. Hold it under an incandescent bulb or in sunlight and white rises
well above lux, because those sources give off far more infrared than an LED lamp does.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
