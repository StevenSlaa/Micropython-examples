# I2C EEPROM (24LC, AT24C, CAT24C)

Reads and writes the 24-series I2C EEPROMs: 24LC01 through 24LC512, AT24C32, CAT24C256 and the
many parts that copy them. Any of them, from any manufacturer — the family has behaved the same
way for decades.

EEPROM keeps what you write with the power off, unlike RAM, and can be rewritten a byte at a
time, unlike the flash your program lives in. It is the right place for a setting, a serial
number, a calibration constant, or a counter that has to survive being unplugged.

## Install

Install it from the Pulsar IoT library panel, or copy `eeprom.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from eeprom import EEPROM

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
memory = EEPROM.for_part(i2c, "CAT24C256")     # or 24LC01, AT24C32, 24c512...

memory.write(0, b"hello")
print(memory.read(0, 5))                        # b'hello'
print(len(memory), "bytes")
```

`for_part()` knows the sizes and page sizes of the whole family. If yours is not in the list, or
is unlabelled, give the numbers directly:

```python
memory = EEPROM(i2c, address=0x50, size=32768, page_size=64)
```

Those two numbers matter. Claiming a chip is bigger than it is means writes wrap silently back
to the start; claiming a page is bigger than it is corrupts the write itself.

## Addresses, and why a scan can mislead you

Most of these chips sit somewhere in `0x50` to `0x57`, chosen by the A0, A1 and A2 pins. Each
pin tied to 3.3V adds to the address, so all three grounded is `0x50`, A0 high is `0x51`, and so
on up to `0x57` with all three high.

**The small parts ignore those pins.** A 24LC01 or 24LC02 has no address selection at all: it
acknowledges every address from `0x50` to `0x57`. One of them on a bus therefore looks exactly
like eight chips to a scanner, and worse, it overlaps every other EEPROM on the bus. Two chips
answering one address both drive the bus on a read, and you get neither.

So a scan finding all eight addresses does not mean eight chips. It usually means one small one.
If you have a 24LC01 or 24LC02 alongside anything else in that range, they cannot share a bus:
put the small one on a second bus, or leave it out.

## What the driver is doing for you

**Page boundaries.** These chips write in pages — 8 bytes on the smallest, 128 on the largest.
A write that runs past the end of a page does not continue into the next one. It wraps back to
the start of the same page and overwrites what it just wrote, with no error. This is the classic
way to lose data on an EEPROM, and the driver splits every write so it cannot happen.

**Write cycles.** After a write the chip stops answering for a few milliseconds while it
commits. The driver knocks on the address until it answers again, which is faster than guessing
at a delay and safer than not waiting at all. A chip that never comes back raises rather than
hanging your program.

Reading has neither restriction: `read()` can cross as many pages as you like in one go.

## Notes

- Writes wear the chip out, slowly: about a million writes per byte. That is endless for a
  setting and a real limit for a counter written every second, which would wear a byte out in a
  fortnight. Write when something changes, not on a timer.
- An erased or new EEPROM reads as `0xff` everywhere, which is a useful "nothing here yet".
- `read()` gives you `bytes`. Text needs encoding on the way in and decoding on the way out:
  `memory.write(0, "hello".encode())`, then `memory.read(0, 5).decode()`.
- Both SDA and SCL need pull-up resistors. Breakout boards have them; a bare chip on a
  breadboard does not, and 4.7k to 3.3V on each is the usual choice.
- The WP pin blocks writes when it is tied high. If reads work and writes silently do nothing,
  check it is grounded.
- The 4K, 8K and 16K parts (24LC04, 08, 16) are the awkward middle of the family: they steal
  bits from the device address to reach their upper memory, so they occupy two, four or eight
  addresses. This driver reaches the first block of those. The rest of the family is complete.

## Tests

`python3 -B drivers/eeprom/test_eeprom.py` runs against a simulated chip that wraps its pages
and goes busy after a write exactly as the hardware does, so the page splitting and the write
polling are checked against the behaviour they exist for, off-board.

Used by: [i2c-eeprom](../../examples/i2c-eeprom)
