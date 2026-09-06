---
example: tm1637-7-segment-display
author: Steven Slaa
---

# TM1637 7-Segment Display Example

In this example the microcontroller writes numbers and a scrolling message to a TM1637 four
digit 7-segment display, and then counts minutes and seconds with a blinking colon.

## Requires
This example needs the [TM1637 7-segment display](../../drivers/tm1637) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The TM1637 uses two wires that look like I2C and are not: same CLK and DIO names, its own
protocol, no addresses, and it will not turn up in an I2C scan. Any two GPIO pins work, and the
pull-up resistors are already on the module.

| TM1637 | ESP32 | Pico |
| --- | --- | --- |
| VCC | 5V | VBUS (5V) |
| GND | GND | GND |
| CLK | 14 | 14 |
| DIO | 12 | 15 |

The module is sold for 5V and is noticeably dim on 3.3V. Running it from 5V while driving CLK
and DIO from a 3.3V board is fine, because those pins are open drain.

## Output

`boot`, then `1234`, then `hello` scrolling past, and then a counter in the form `01:23` with
the colon blinking once a second.

Nothing has set the board's clock, so that counter starts from whenever the board was powered
up rather than telling the real time. Connecting to the network and calling `ntptime.settime()`,
or adding an RTC module, turns the same code into a clock — swap `now[4], now[5]` for
`now[3], now[4]` to show hours and minutes.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
