---
driver: max7219
author: Mike Causer
---

# MAX7219 LED matrix

Driver for chained MAX7219 8x8 LED matrix modules over SPI. A common 4-in-1 board is four
modules in a row, giving a 32x8 display of one buffer, so text simply spans the joins.

`Matrix8x8` wraps a [`framebuf.FrameBuffer`](https://docs.micropython.org/en/latest/library/framebuf.html)
and forwards its drawing primitives: `fill`, `pixel`, `line`, `hline`, `vline`, `rect`,
`fill_rect`, `text`, `scroll` and `blit`.

## Install

Install it from the Pulsar IoT library panel, or copy `max7219.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SPI
from max7219 import Matrix8x8

spi = SPI(1, baudrate=10000000, polarity=1, phase=0, sck=Pin(18), mosi=Pin(23))
display = Matrix8x8(spi, Pin(5), 4)      # 4 chained modules, 32x8 pixels

display.brightness(3)
display.fill(0)
display.text("Hi!", 0, 0, 1)
display.show()                            # nothing appears until show()
```

Scrolling a message across the chain:

```python
message = "MicroPython "
while True:
    for offset in range(len(message) * 8):
        display.fill(0)
        display.text(message, -offset, 0, 1)
        display.show()
        sleep(0.05)
```

The built-in font is 8x8, so a 4 module chain fits exactly four characters at a time.

## When the display looks wrong

These boards are wired in more than one way and none of them announce which. The display
working but looking scrambled is a wiring difference, not a fault:

| What you see | Try |
| --- | --- |
| Text reads back to front, last character first | `Matrix8x8(spi, cs, 4, reverse=True)` |
| Characters lie on their side | `Matrix8x8(spi, cs, 4, transpose=True)` |
| Both | pass both |
| Only the first module lights | `num` is wrong, or DOUT of one module is not wired to DIN of the next |
| Nothing at all, or every LED on | check CS, and that the modules have their own 5V |

## Notes

- Wiring is SPI plus a chip select: VCC to 5V, GND, DIN to MOSI, CS to any GPIO, CLK to SCK.
  There is no MISO; the chain never talks back, which is why a wrong `num` cannot be detected.
- The modules run on 5V but their inputs are happy with 3.3V logic from an ESP32 or a Pico.
- Current adds up. One module at full brightness with every LED on is around 300mA, so four
  chained can pull over an amp — more than a USB port will give you. Start at a low brightness
  and power long chains separately, sharing the ground with the board.
- `brightness(0)` is dim but not off, and it applies to the whole chain. Use `fill(0)` and
  `show()` to blank the display.
- Everything is drawn into memory; `show()` is what pushes it out.
- Chain them by wiring each module's DOUT to the next module's DIN. `num` counts modules, not
  pixels, and the buffer is `8 * num` bytes.

## Tests

`python3 -B drivers/max7219/test_max7219.py` checks the chain ordering, the brightness command
and the row and column swap, off-board.

Used by: [spi-led-matrix-max7219](../../examples/spi-led-matrix-max7219)

## Credits

From [mcauser/micropython-max7219](https://github.com/mcauser/micropython-max7219), MIT,
Copyright 2017 Mike Causer. The `reverse` and `transpose` options were added for the 4-in-1
boards that are wired differently.
