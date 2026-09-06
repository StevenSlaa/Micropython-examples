---
example: i2c-eeprom
author: Steven Slaa
---

# I2C EEPROM Example

In this example the microcontroller keeps a boot counter in an I2C EEPROM, so that it goes up
every time the board is reset — including after the power has been cut, which is the whole point.
It then writes and reads back a message, and checks that a long write across page boundaries
survives intact.

Works with any of the 24-series EEPROMs: 24LC01, AT24C32, CAT24C256 and the rest.

## Requires
This example needs the [I2C EEPROM](../../drivers/eeprom) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| EEPROM | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SDA | 21 | 0 |
| SCL | 22 | 1 |
| A0, A1, A2 | GND for address 0x50 | GND for address 0x50 |
| WP | GND | GND |

A bare chip on a breadboard needs a 4.7k resistor from SDA to 3.3V and another from SCL; a
breakout board already has them.

**WP must be grounded.** Tied high it blocks writes, and the symptom is confusing: reads work
perfectly and writes appear to do nothing at all.

Each of A0, A1 and A2 tied to 3.3V instead of GND adds to the address, so `0x50` with all three
low through to `0x57` with all three high. Set `address` at the top of the script to match.

## Output

First run on a new chip:

```
Found a CAT24C256: 32768 bytes
This chip has never been written to
This board has now booted 1 times
Wrote: Stored at 1 boots
Read back: Stored at 1 boots
200 bytes across page boundaries read back correctly: True
Reset the board to watch the counter go up
```

Pull the power out, plug it back in, and the count carries on from where it was. That is the
difference between EEPROM and every variable in your program.

## If a scan finds more chips than you have

An I2C scan showing all eight of `0x50` to `0x57` usually means one small chip, not eight. A
24LC01 or 24LC02 has no address pins and answers to every address in that range.

That also means a small chip cannot share a bus with any other EEPROM: both will answer the same
address, both will drive the bus on a read, and you will get neither. Put it on its own bus, or
use one chip at a time.

## Things worth knowing

- EEPROM wears out after roughly a million writes to any one byte. That is forever for a
  setting, and about a fortnight for a counter written every second. Write when something
  changes, not on a timer — which is why this example writes once per boot.
- A new chip reads as `0xff` everywhere, which makes a useful "nothing stored here yet".
- The chip stores bytes. Text has to be encoded going in and decoded coming out, and you have to
  remember how long it was — or store the length alongside it.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
