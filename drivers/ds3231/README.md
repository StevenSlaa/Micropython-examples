# DS3231 real time clock

Reads and sets the DS3231, the accurate real time clock module with a coin cell on the back. Its
crystal is temperature compensated, so it drifts by a couple of minutes a year rather than the
several minutes a week you get from the cheaper DS1307.

A microcontroller forgets the time whenever it loses power, and knows nothing about it at boot
unless it has a network. This module remembers.

## Install

Install it from the Pulsar IoT library panel, or copy `ds3231.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from ds3231 import DS3231

clock = DS3231(SoftI2C(scl=Pin(22), sda=Pin(21)))

# Once, to set it. Afterwards the coin cell keeps it running.
clock.datetime = (2026, 9, 6, 14, 32, 0, 6)   # year, month, day, hour, minute, second, weekday

print(clock.datetime)
print(clock.temperature, "C")
```

Times are 7-tuples of `(year, month, day, hour, minute, second, weekday)`, with weekday 0 for
Monday, matching what `time.localtime()` gives you. The weekday is optional when setting.

At boot, hand the time to the board so everything else works normally:

```python
clock.sync_board()          # sets machine.RTC
print(time.localtime())     # now correct
```

## Has it actually been set?

The chip records whether its oscillator has ever stopped, which is the difference between a
time and a number that looks like one:

```python
if clock.lost_power:
    print("The clock is not set, or the battery is flat")
else:
    clock.sync_board()
```

It reads true on a module that has never been set and on one whose battery went flat or was
removed. Setting the time clears it. A driver that ignores this flag returns 2000-01-01, or
worse, something plausible.

## Notes

- The address is `0x68` and cannot be changed. Most modules also carry an AT24C32 EEPROM at
  `0x57`, which is a separate chip this driver knows nothing about, so an I2C scan finding two
  devices is normal.
- The temperature is the chip measuring itself, to compensate its crystal. It reads a degree or
  two above the room because of its own package, so treat it as the module's temperature, not
  the air's.
- **Do not put a rechargeable cell in a module wired for a CR2032.** Many boards ship with a
  charging resistor fitted for a LIR2032. Feeding a non-rechargeable CR2032 through it is the
  usual reason one of these modules leaks or gets hot. Removing that resistor is the common fix.
- `aging_offset` trims the crystal at roughly 0.1 parts per million per step. A clock gaining a
  second a week is about 1.6ppm fast, so a positive offset of about 16 slows it down. Change it
  once you have measured the drift over a week, not before.
- 32K and SQW output pins and the two alarms are not exposed. The registers are there in the
  datasheet if you need them.

## Tests

`python3 -B drivers/ds3231/test_ds3231.py` checks the binary coded decimal handling, the flag
bits sharing those registers, the signed temperature and the aging offset, off-board.

Used by: [i2c-rtc-ds3231](../../examples/i2c-rtc-ds3231)
