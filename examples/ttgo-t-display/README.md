---
example: ttgo-t-display
author: Steven Slaa
---

# TTGO T-Display v1.1 (1.14 inch SPI LCD)

In this example the LilyGO/TTGO T-Display v1.1 (the original ESP32 board, not the S3) draws an
illustrative dashboard on its built-in colour LCD: the Pulsar IoT logo, a reading, a live chart and
a press counter. The board's two buttons page through them.

The display is a 135x240 ST7789V on SPI. The [st7789py](../../drivers/st7789py) driver supports
this size out of the box: pass `135, 240` and it applies the panel's offsets and colour inversion
itself.

## Requires

This example needs the [ST7789 display](../../drivers/st7789py) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy `st7789py.py` into `/lib` on
> the microcontroller yourself. This example does not use the driver's `vga2_16x32.py` font: at
> 16x32 it turns every heading into a shouted word on a screen this size.

`pulsar_ui.py`, next to the script, holds the artwork. The IDE copies it to the board with the
script.

## Connections

Nothing to wire: the LCD and both buttons are built into the board.

| Signal | GPIO |
| --- | ---: |
| SCK | 18 |
| MOSI | 19 |
| Chip select | 5 |
| Data/command | 16 |
| Reset | 23 |
| Backlight | 4 |
| Left button | 0 |
| Right button | 35 |

## The buttons

- **Right button**: the next page. The dot beside the logo shows which one you are on.
- **Left button**: what that page does with it. On **TEMPERATURE** it switches between °C and °F.

Both are read as the moment they go down, not as being held, so one press counts once however long
you lean on it.

## The pages

1. **TEMPERATURE** — a made-up reading in large Poppins digits, with a bar underneath.
2. **LIVE TEMP** — the same reading as a chart that scrolls to the left, the line drawn over a
   dimmed red area.
3. **BUTTONS** — how often each button has been pressed, red for the left one and green for the
   right, each with a bar that wraps round every hundred presses.

The readings are made up; nothing is measured. Put a real sensor's reading in `reading` and it
becomes a real dashboard.

## How it stays smooth

The driver is pure Python, so a full screen is 26 ms on its own. The dashboard therefore avoids
drawing anything twice:

- **The logo is drawn once**, at startup. A page change only repaints the three dots.
- **A page draws its heading once** when you arrive, then only the numbers that changed. A number
  is drawn straight over the old one and the rest of the row is wiped, so nothing has to blink.
- **The chart lives in memory**, a 228x56 `framebuf.FrameBuffer`. Each frame framebuf's `scroll()`
  slides it 3 pixels left, only those 3 new columns are drawn, and it reaches the screen in one
  `blit_buffer`, so it never shows half a frame.
- **Bitmaps and headings go through a lookup table.** `lut_for()` turns a whole byte of a 1-bit
  bitmap into 8 pixels at once; pixel by pixel in Python is about ten times slower. A table costs
  4KB, so the example keeps to a handful of colour pairs.
- **The number is redrawn four times a second**, not twenty. Drawing it costs 40 ms, and a figure
  that changes twenty times a second cannot be read anyway.

framebuf keeps each colour's two bytes the other way round from the display, which is why the
chart's colours are swapped once, as `INK_...`.

## The text

The driver's own font is 16x32, too big here for anything but a single word. Headings are drawn
instead with framebuf's built-in 8x8 font at double size: `label()` writes the characters into a
1-bit buffer and widens each row through the same lookup table the bitmaps use, repeating every
row twice. Captions stay at 8x8 by passing `scale=1`. Only the numbers use the large Poppins
characters.

## The artwork

`pulsar_ui.py` is the same artwork as in the [e-paper](../spi-epaper-ssd1680) and
[T-Display S3](../ttgo-t-display-s3) examples: the logo on one line and large Poppins characters
for the numbers, as 1 bit bitmaps. They were made on a computer from the logo's SVG and the Poppins
font, because the board has neither.

Any black and white image works the same way: turn it into `MONO_HLSB` bytes, 8 pixels a byte, and
hand them to `mono()` with a width, a height and two colours.

## Output

Every twentieth frame the script prints how long the last one took to draw:
```
Frame: 202 ms
Frame: 1 ms
Frame: 57 ms
Frame: 19 ms
```

The first frame builds a lookup table. After that a frame costs what it draws: 1 ms when nothing
changed, 19 ms for a chart step, and up to about 60 ms when a whole number is redrawn. A page
change takes 70 to 120 ms, and nearly 300 ms the first time, when the heading colour's table has
to be built.

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Screen stays black | `st7789py.py` is not in `/lib`; watch the REPL for an error |
| `ImportError: no module named 'pulsar_ui'` | `pulsar_ui.py` must be on the board next to the script |
| The picture is upside down | set `rotation = 3` instead of 1 |
| The layout is cut off | `rotation` is 0 or 2, which is portrait; use 1 or 3 |
| `MemoryError` | reset the board, or run the script on its own: the chart alone is 25 KB |
| The board reboots at startup | `baudrate` above 26666666 crashes this board; see the comment |

## Plotter

The only number printed is the frame time, so the plotter draws a line near zero with a spike
whenever something is redrawn.

## Tested

- TTGO T-Display v1.1 running MicroPython 1.29.0, at 240MHz with the bus at 26.67MHz: 180 frames
  across all three pages with never less than 26 KB of memory free. A full screen fill takes 26 ms,
  a chart step 19 ms, a page change 70 to 120 ms.
