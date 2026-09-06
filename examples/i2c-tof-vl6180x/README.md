# VL6180X Sensor Example

In this example the microcontroller measures the distance to a nearby object with a VL6180X time
of flight sensor and prints it in millimetres, along with the ambient light level the same chip
reports. Unlike the ultrasonic and infrared distance sensors, this one times a pulse of light,
so a black object reads much the same as a white one — but it only reaches about 10cm, or 20cm
against something white and matt.

## Requires
This example needs the [VL6180X range and light](../../drivers/vl6180x) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The breakout runs on 3.3V and sits at I2C address `0x29`, which cannot be changed with a solder
bridge. GPIO0 (chip enable) and GPIO1 (interrupt) are not used here.

| VL6180X | ESP32 | Pico |
| --- | --- | --- |
| VIN | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

## Output
```
Distance: 43 mm  Light: 214 lux
Distance: 41 mm  Light: 213 lux
Distance: 8 mm  Light: 66 lux
No reading: no convergence, nothing in range
Distance: 96 mm  Light: 228 lux
```

The sensor returns a number even when nothing is in front of it, so the example checks
`range_status` before believing the distance. With an empty view that status is 7, *no
convergence*, and the millimetres are meaningless.

If every line is an error, the sensor is working but seeing nothing come back. Check the clear
protective sticker is off the two windows, and hold a sheet of white paper about 5cm away —
this part reaches roughly 10cm, so a wall across the room reads as an error rather than as a
large number. The [driver README](../../drivers/vl6180x) has the rest of the list.

Readings are a few millimetres out from one sensor to the next. Put something at a distance you
have measured, and set `offset` at the top of the script to the difference.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
