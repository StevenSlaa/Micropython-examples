# SPI LED Matrix (MAX7219) Example

In this example the microcontroller writes text to a chain of MAX7219 8x8 LED matrix modules and
then scrolls a message across them. The chain is treated as one display, so a message runs
across the joins between modules.

## Requires
This example needs the [MAX7219 LED matrix](../../drivers/max7219) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The modules take 5V, and their inputs are happy with 3.3V logic from an ESP32 or a Pico. There
is no MISO: the chain never answers, which is why the number of modules has to be told to the
driver rather than detected.

| Matrix | ESP32 | Pico |
| --- | --- | --- |
| VCC | 5V | VBUS (5V) |
| GND | GND | GND |
| DIN | 23 (MOSI) | 19 (MOSI) |
| CS | 5 | 17 |
| CLK | 18 (SCK) | 18 (SCK) |

Set `spi_id` at the top of the script to 2 on an ESP32 or 0 on a Pico. Extra modules chain from
one board's DOUT to the next board's DIN; a 4-in-1 board has done that for you internally.

## Output

`Hi!` for two seconds, then the message scrolling right to left forever. The 8x8 font means four
chained modules show four characters at a time.

## If it looks wrong

The display working but looking scrambled is a wiring difference between board makers, not a
fault. Both switches are at the top of the script:

| What you see | Change |
| --- | --- |
| Text reads back to front | `reverse = True` |
| Characters lie on their side | `transpose = True` |
| Both | set both |
| Only the first module lights up | `modules` is wrong for your board |

## Power

Brightness starts at 2 on purpose. One module with every LED lit at brightness 15 is around
300mA, so four chained can ask for over an amp, which is more than a USB port will supply — the
board browns out and resets. Power a long chain from its own 5V supply, with the grounds joined.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
