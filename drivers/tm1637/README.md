---
driver: tm1637
author: Mike Causer
---

# TM1637 7-segment display

Driver for the common four digit 7-segment LED modules built around the TM1637, including the
ones with a colon in the middle for showing a time.

The TM1637 uses **two wires that are not I2C**, despite looking like it: same CLK and DIO names,
same pull-ups, but its own protocol and no addresses. An I2C scan will not find it. Any two
GPIO pins will do.

## Install

Install it from the Pulsar IoT library panel, or copy `tm1637.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
import tm1637

display = tm1637.TM1637(clk=Pin(14), dio=Pin(12))

display.number(1234)            # right aligned, -999 to 9999
display.numbers(12, 59)         # 12:59, with the colon lit
display.show("cool")            # letters, where the seven segments allow
display.scroll("hello world")   # walks a longer message across
display.brightness(3)           # 0 to 7
```

Other things it can do:

```python
display.temperature(22)         # 22°C, using the last two digits for the unit
display.hex(0xbeef)             # hexadecimal
display.write([0b00111111, 0b00000110])   # raw segments, bit per segment
display.write([0])              # blank the first digit
```

Modules with a decimal point after every digit instead of a colon use the other class, which
understands `.` in a string:

```python
display = tm1637.TM1637Decimal(clk=Pin(14), dio=Pin(12))
display.show("3.14")
```

## Notes

- Not I2C. It will not appear in an I2C scan, and it cannot share a bus with I2C devices; give
  it two pins of its own.
- The colon is the top bit of the second digit, which is why `numbers()` has a `colon` argument
  and `show()` takes `colon=True`. On modules without a colon that bit is the decimal point.
- Seven segments cannot make every letter. `encode_string` covers 0-9, a-z, space, dash and
  star, and the results for k, m, v, w and x are approximations at best.
- The modules are sold for 5V and are noticeably dim on 3.3V. Powering the module from 5V while
  driving CLK and DIO from a 3.3V board works, because the pins are open drain with the pull-ups
  already on the module.
- `brightness(0)` is the dimmest setting, not off. Write blank segments to clear the display.
- `scroll()` blocks for the whole message: it sleeps between frames rather than returning.

Used by: [tm1637-7-segment-display](../../examples/tm1637-7-segment-display)

## Credits

From [mcauser/micropython-tm1637](https://github.com/mcauser/micropython-tm1637), MIT,
Copyright 2016-2023 Mike Causer, vendored unchanged.
