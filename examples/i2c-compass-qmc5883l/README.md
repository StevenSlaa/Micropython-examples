---
example: i2c-compass-qmc5883l
author: Steven Slaa
---

# QMC5883L Compass Example

In this example the microcontroller reads a QMC5883L twice a second and prints the magnetic
field on three axes in microtesla, along with a compass heading in degrees.

The QMC5883L is a three axis magnetometer: a sensor that measures magnetic fields. The earth's
field points north, so with the sensor held flat it works as a digital compass. It is the chip on
the HW-246 and most GY-271 modules. The [driver README](../../drivers/qmc5883l) explains more.

## Requires
This example needs the [QMC5883L magnetometer](../../drivers/qmc5883l) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The sensor sits at I2C address `0x0D`. If `i2c.scan()` finds `0x1E` instead, your module carries
the older HMC5883L; use the [GY-271 compass example](../i2c-compass-gy271) for that one.

| QMC5883L module | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

DRDY is not used.

## Output
```
X: 21.4 uT  Y: -8.3 uT  Z: -42.1 uT  Heading: 339 degrees
X: 22.0 uT  Y: -6.9 uT  Z: -42.4 uT  Heading: 343 degrees
X: 19.8 uT  Y: -11.5 uT  Z: -41.8 uT  Heading: 330 degrees
X: 266.7 uT  Y: 266.7 uT  Z: -266.7 uT  Heading: 45 degrees  <- overflow
```

## Calibration

Straight out of the box the heading can be tens of degrees out, because the sensor reads
whatever iron and magnets are near it as well as the earth. Set `calibrating = True` at the top
of the script, run it, and turn the module slowly through every orientation for twenty seconds.
Paste the printed `offset` and `scale` back into the script and set `calibrating` to False.

The heading also assumes the module is held flat. Tilt it and the reading swings.

## Plotter

Open the **Plotter** tab beside the REPL to graph the three axes and the heading. Turning the
module through a full circle draws two sine waves a quarter cycle apart, which is what a
compass is underneath. The heading runs 0 to 360 and so dominates the scale — delete it from
the print to look at the field on its own.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
