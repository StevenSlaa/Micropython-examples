---
example: hx711-scale
author: Steven Slaa
---

# HX711 Load Cell Scale Example

In this example the microcontroller turns a load cell and an HX711 amplifier into a scale. It
tares on start, calibrates against a weight you know, then prints the weight in grams.

A load cell is a metal bar with strain gauges glued on: it bends a tiny amount under load and
its resistance changes with it. The HX711 is the amplifier and 24 bit converter that makes that
change big enough to measure. The [driver README](../../drivers/hx711) explains more.

## Requires
This example needs the [HX711 load cell amplifier](../../drivers/hx711) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| HX711 | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| DT | 16 | 14 |
| SCK | 17 | 15 |

On a Pico, set `dout_pin = 14` and `sck_pin = 15` at the top of the script.

The load cell's four wires go to the HX711's E+, E-, A- and A+. The usual colours are:

| Load cell | HX711 |
| --- | --- |
| red | E+ |
| black | E- |
| white | A- |
| green | A+ |

Colours vary between makers. If the weight comes out negative it still works, since
calibration takes care of it, but swap white and green for positive raw readings.

Mount the load cell so it can bend: one end screwed to a base, the other to the platform, with
the arrow on the bar pointing the way the load pushes.

## Using it

1. Start with the scale empty. It tares for a second.
2. Put the calibration weight (500 g unless you change `calibration_weight`) on within 10
   seconds.
3. It prints a line like `Calibrated: set  scale = 419.83  at the top ...`. Copy that number
   into `scale` at the top of the script so the next start skips calibration.

The scale still tares on every start, because a load cell's zero drifts.

## Output
```
Taring: keep the scale empty
Place 500 g on the scale, measuring in 10 seconds
Calibrated: set  scale = 419.83  at the top to skip this next time
Weight:    500.1 g
Weight:    499.9 g
Weight:      0.0 g
Weight:    248.6 g
```

## Tuning it

If the reading jumps around, raise `samples` for a steadier but slower reading. If an empty
scale flickers around zero, raise `zero_band`; a 50 kg bathroom scale cell may need 20 g or
more, a 1 kg cell 0.5 g. Calibrate with a weight close to what you plan to measure, and at least
a tenth of the load cell's rating.

## Plotter

Open the **Plotter** tab beside the REPL to graph the weight. Press on the platform with a finger
and watch the line follow; set a heavy weight down and it jumps up, then creeps a gram or two as
the load cell settles.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
