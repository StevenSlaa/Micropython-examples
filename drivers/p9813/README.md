# P9813 RGB LED driver

Drives chains of P9813 constant current RGB LEDs — chainable RGB LED modules, and the RGB strips
that come with **four** wires plus a clock rather than the three of a WS2812B strip.

The P9813 has a clock line, so unlike the WS2812B it does not care how fast or how evenly you
send the bits. That makes it forgiving on a busy board, at the cost of one more wire.

## Install

Install it from the Pulsar IoT library panel, or copy `p9813.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from p9813 import P9813

leds = P9813(clock=Pin(14), data=Pin(13), n=2)

leds[0] = (255, 0, 0)      # red, green, blue
leds[1] = (0, 128, 255)
leds.write()               # nothing changes until write()

leds.fill((0, 0, 0))
leds.brightness = 0.3      # applied when written, so it dims the whole chain at once
leds.write()
```

## Wiring

| Module | Goes to |
| --- | --- |
| CI / CLK | any GPIO |
| DI / SDA | any GPIO |
| VCC | 5V |
| GND | GND, shared with the board |

Chains run from one module's CO and DO to the next module's CI and DI. Data only travels one
way, so a chain wired into the out end lights nothing at all.

## Notes

- The chips are 5V, but their inputs accept 3.3V logic from an ESP32 or a Pico. The grounds
  have to be joined.
- Each frame is 32 zero bits, four bytes per LED, then 32 more zero bits. The first of those
  four bytes is a checksum carrying the inverted top two bits of each colour, which is how the
  chip tells a real frame from noise. `checksum()` is exported if you are debugging a capture.
- Colours go down the wire as blue, green, red. The driver takes and returns `(red, green,
  blue)` like everything else, and swaps them for you.
- These are constant current drivers, so brightness does not sag as the chain gets longer, and
  a long chain draws real current: up to about 60mA per LED at white. Power a long strip from
  its own 5V supply.
- Shifting is bit banged at a few kHz, which is fine for a chain being watched by a person. For
  a frame rate, wire the clock and data lines to SCK and MOSI and drive them from `machine.SPI`.
- For three-wire WS2812B or SK6812 strips, use the [pixels](../pixels) driver instead. They look
  similar and are not compatible.

## Tests

`python3 -B drivers/p9813/test_p9813.py` decodes the bit stream back into bytes and checks the
frame layout, the checksum byte and the channel order, off-board.

Used by: [p9813-rgb-led](../../examples/p9813-rgb-led)
