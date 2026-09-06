# I2C Compass (GY-271) Example

In this example the microcontroller reads the magnetic field from a GY-271 or HW-246 compass
module and prints the three axes in microtesla along with a heading in degrees.

## Requires
This example needs the [GY-271 compass (QMC5883L / HMC5883L)](../../drivers/gy271) driver
installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The module runs on 3.3V. Boards sold as GY-271 carry either a QMC5883L at address `0x0d` or an
HMC5883L at `0x1e`; the example detects which and prints it, so you do not have to know.

| GY-271 | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

DRDY is not used.

## Output
```
Found a QMC5883L at 0x0d
X: 21.4 uT  Y: -8.3 uT  Z: -42.1 uT  Heading: 339 degrees
X: 22.0 uT  Y: -6.9 uT  Z: -42.4 uT  Heading: 343 degrees
X: 19.8 uT  Y: -11.5 uT  Z: -41.8 uT  Heading: 330 degrees
```

## Calibration

Straight out of the box the heading can be tens of degrees out, because the sensor reads
whatever iron and magnets are near it as well as the earth. Set `calibrating = True` at the top
of the script, run it, and turn the module slowly through every orientation for twenty seconds.
Paste the printed `offset` and `scale` back into the script and set `calibrating` to False.

The heading also assumes the module is held flat. Tilt it and the reading swings.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
