# VCNL4040 Sensor Example

In this example the microcontroller reads a VCNL4040 and prints how close something is, how
bright the room is in lux, and the white light channel, flagging anything that comes near.

Proximity here is a count, not a distance. It rises as an object approaches and how fast depends
on how reflective that object is, so a white sleeve reads much nearer than a black one at the
same distance. For millimetres, use the [VL6180X example](../i2c-tof-vl6180x) instead.

## Requires
This example needs the [VCNL4040 proximity and light](../../drivers/vcnl4040) driver installed
on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The breakout runs on 3.3V and sits at I2C address `0x60`, which is fixed. The INT pin is not
used here.

| VCNL4040 | ESP32 | Pico |
| --- | --- | --- |
| VIN | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

## Output
```
Proximity:     3  Light:  214.5 lux  White:   289
Proximity:    58  Light:  201.2 lux  White:   271
Proximity:   412  Light:   88.7 lux  White:   119 <- near
Proximity:  2867  Light:    6.1 lux  White:     9 <- near
Proximity:     4  Light:  213.9 lux  White:   288
```

The light reading falls as a hand approaches, because the hand is also blocking the room.

## Tuning it

Watch the numbers with your hand where you want the trigger to fire, and set `near` at the top
of the script to something below what you saw.

If proximity never settles near zero with nothing in front of the sensor, it is seeing its own
LED reflected off a window or a case. Note what it reads with the view clear and put that number
in `cancellation`.

## Plotter

Open the **Plotter** tab beside the REPL to graph proximity against the light level. Moving a
hand in shows the two run opposite ways, as the hand both reflects the LED and shades the room.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
