---
example: mux-74hc4051
author: Steven Slaa
---

# 74HC4051 Multiplexer

In this example the microcontroller reads eight analog inputs through a single analog pin, using
a 74HC4051, and prints the voltage on each of them twice a second.

The 74HC4051 is an electronic rotary switch. Three pins from the board choose which of its eight
inputs, Y0 to Y7, is connected to its common pin Z, and Z goes to one analog pin. The driver
steps through the channels and reads each in turn. The [driver README](../../drivers/mux74hc4051)
explains more.

## Requires
This example needs the [74HC4051 analog multiplexer](../../drivers/mux74hc4051) driver installed
on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| 74HC4051 | ESP32 | Pico |
| --- | --- | --- |
| VCC (pin 16) | 3V3 | 3V3 |
| GND (pin 8) | GND | GND |
| VEE (pin 7) | GND | GND |
| S0 (pin 11) | 16 | 2 |
| S1 (pin 10) | 17 | 3 |
| S2 (pin 9) | 18 | 4 |
| E (pin 6) | 19 | 5 |
| Z (pin 3) | 34 | 26 |

The script is set up for an ESP32. On a Pico, change the pin numbers at the top to the ones in
the Pico column. On an ESP32-S3, put Z on one of GPIO 1 to 10.

Then connect what you want to measure to Y0 to Y7. To try it out, use potentiometers: the outer
legs to 3V3 and GND, the middle leg to a channel. Connect channels you do not use to GND, or they
will print random values.

**Power the chip from 3V3, not 5V.** Whatever is on a channel ends up on the board's analog pin,
and that pin takes 3.3V at most.

No enable wire to spare? Connect E to GND and set `enable_pin = None`.

## Output
```
Y0: 0.00 V  Y1: 1.65 V  Y2: 3.30 V  Y3: 0.84 V  Y4: 0.00 V  Y5: 0.00 V  Y6: 0.00 V  Y7: 0.00 V
Y0: 0.00 V  Y1: 1.71 V  Y2: 3.30 V  Y3: 0.84 V  Y4: 0.00 V  Y5: 0.00 V  Y6: 0.00 V  Y7: 0.00 V
Y0: 0.00 V  Y1: 1.98 V  Y2: 3.30 V  Y3: 0.83 V  Y4: 0.00 V  Y5: 0.00 V  Y6: 0.00 V  Y7: 0.00 V
```

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Every channel shows the same value | S0 to S2 are not connected, or E is high: check E is on its pin or on GND |
| Values jump around randomly | nothing connected to that channel; connect unused channels to GND |
| A channel follows the one before it | the sensor cannot charge the ADC quickly. Pass `settle_ms=10` to `Mux74HC4051` |
| Channels come out in the wrong order | S0 and S2 swapped. S0 is the lowest bit |
| An ESP32 stops at about 2.5V | the `adc.atten` line did not run |

## Plotter

Open the **Plotter** tab beside the REPL. It graphs four series at most, so set `channels` at the
top of the script to the four you want, for example `channels = (0, 1, 2, 3)`. Turn one
potentiometer and only its line moves; if another line moves along with it, see the
troubleshooting table.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
