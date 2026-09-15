---
example: i2c-light-bh1750
author: Steven Slaa
---

# BH1750 (GY-30) Light Sensor Example

In this example the microcontroller reads a BH1750 twice a second and prints how bright it is in
lux.

The BH1750 is a digital light sensor from ROHM that measures brightness the way the human eye
sees it and reports it in lux. The GY-30 is the small module it usually comes on, with a voltage
regulator and pull-up resistors already fitted. The [driver README](../../drivers/bh1750)
explains more.

## Requires
This example needs the [BH1750 ambient light (GY-30)](../../drivers/bh1750) driver installed on
the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The sensor sits at I2C address `0x23` with ADDR left open. The GY-30 accepts 5V, but wire VCC to
3V3 so its pull-up resistors keep the I2C lines at 3.3V.

| GY-30 | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SCL | 22 | 1 |
| SDA | 21 | 0 |
| ADDR | not connected | not connected |

## Output
```
Light:    312.5 lux
Light:    310.8 lux
Light:     41.7 lux
Light:      0.8 lux
Light:  54612.5 lux  <- saturated
```

## Tuning it

If it says `<- saturated`, the light is too bright for the setting and the lux reading is too
low. Set `mtreg` to 31 at the top of the script, which reaches about 120 000 lux. If a dark room
only reads in whole lux steps, set `mode` to `CONTINUOUS_HIGH_2` and `mtreg` to 254. The
[driver README](../../drivers/bh1750) has the details.

## Plotter

Open the **Plotter** tab beside the REPL to graph the light level. Cover the sensor with your
hand and it drops to near zero; hold it under a lamp and watch it climb. Under some LED and
fluorescent lights the line stays smooth even though the light flickers, because each reading
averages over 120ms.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
