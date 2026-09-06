---
example: i2c-rtc-ds3231
author: Steven Slaa
---

# I2C RTC (DS3231) Example

In this example the microcontroller reads the date, time and temperature from a DS3231 real time
clock module, and copies the time into the board's own clock so `time.localtime()` is right for
everything else in the program.

A microcontroller has no idea what time it is at boot. This module, with its coin cell, does.

## Requires
This example needs the [DS3231 real time clock](../../drivers/ds3231) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| DS3231 | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |

SQW and 32K are not used here. An I2C scan usually finds two devices: `0x68` is the clock, and
`0x57` is the EEPROM chip most of these modules also carry.

## Setting it

A new module has never been told the time, and says so. On the first run the script prints:

```
The clock is not set. Put a time in set_time at the top of this script and run it.
```

Put the current time in `set_time` at the top, run it once, then set it back to `None`. The coin
cell keeps it going from then on, through resets and power cuts.

## Output
```
Clock set
Board clock set from the module
2026-09-06 14:32:00  Temperature: 27.25 C
2026-09-06 14:32:01  Temperature: 27.25 C
2026-09-06 14:32:02  Temperature: 27.50 C
```

The temperature is the chip measuring its own package to compensate its crystal, so it sits a
degree or two above the room.

## Plotter

Open the **Plotter** tab beside the REPL to graph the temperature. The date and time have no
letters in them, so the plotter takes only the named value from each line and leaves the
timestamp alone.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
