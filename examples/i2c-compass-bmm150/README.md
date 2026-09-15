---
example: i2c-compass-bmm150
author: Steven Slaa
---

# BMM150 Compass Example

In this example the microcontroller reads a BMM150 twice a second and prints the magnetic field
on three axes in microtesla, along with a compass heading in degrees.

The BMM150 is a tiny three axis magnetometer from Bosch: a sensor that measures magnetic fields.
The earth's field points north, so with the sensor held flat it works as a digital compass. The
[driver README](../../drivers/bmm150) explains more.

## Requires
This example needs the [BMM150 magnetometer](../../drivers/bmm150) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The chip runs on 1.62V to 3.6V, so wire VCC to 3V3. Breakouts differ in which address they
ship at, from `0x10` to `0x13`. If the script says `No BMM150 at 0x10`, run the
[I2C scanner](../i2c-scanner) and put the address it finds in `address` at the top of the script.

| BMM150 breakout | ESP32 | Pico |
| --- | --- | --- |
| VCC / 3V3 | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

Leave CS, SDO and DRDY/INT unconnected unless your breakout's documentation says otherwise; CS
and SDO are what set the address.

## Output
```
X: 12.6 uT  Y: 20.4 uT  Z: 44.0 uT  Heading: 58 degrees
X: 13.7 uT  Y: 20.4 uT  Z: 44.0 uT  Heading: 58 degrees
X: 13.0 uT  Y: 20.4 uT  Z: 44.7 uT  Heading: 58 degrees
Out of range  <- overflow, is there a magnet nearby?
```

## Calibration

Straight out of the box the heading can be tens of degrees out, because the sensor reads
whatever iron and magnets are near it as well as the earth. The chip's factory trim does not fix
that: it corrects the chip, not its surroundings. Set `calibrating = True` at the top of the
script, run it, and turn the module slowly through every orientation for twenty seconds. Paste
the printed `offset` and `scale` back into the script and set `calibrating` to False.

The heading also assumes the module is held flat. Tilt it and the reading swings. If the heading
runs backwards or is 90 degrees off, check the X and Y markings on your breakout and point X
north.

## Plotter

Open the **Plotter** tab beside the REPL to graph the three axes and the heading. Turning the
module through a full circle draws two sine waves a quarter cycle apart, which is what a
compass is underneath. The heading runs 0 to 360 and so dominates the scale — delete it from
the print to look at the field on its own.

## Tested
- Raspberry Pi Pico (RP2040), MicroPython 1.28.0, `SoftI2C` on GP6 (SDA) and GP7 (SCL) at
  100 kHz, breakout at address `0x13`. Uncalibrated, it read a total field of about 51µT, which
  is right for the earth's field in the Netherlands.
