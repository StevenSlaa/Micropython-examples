---
example: ttgo-t-display-s3
author: Steven Slaa
---

# TTGO T-Display S3 (1.9 inch 8-bit LCD)

In this example the LilyGO/TTGO T-Display-S3 draws an illustrative, animated dashboard on its
built-in colour LCD: the Pulsar IoT logo, three cards with readings and a live chart that scrolls,
at 25 frames a second.

The display is a 170x320 ST7789 connected to the ESP32-S3 over an 8-bit parallel bus, not SPI. That
bus is fast: a full-screen fill takes about 21 ms, so a dashboard can move smoothly without
flicker. The [driver README](../../drivers/st7789-parallel) explains more.

## Requires

This example needs two drivers installed on the board:

- [ST7789 8-bit parallel display](../../drivers/st7789-parallel), which talks to the display
- [RGB565 display drawing (shared)](../../drivers/rgb565-display), with the drawing methods

> Install them from the library panel in the Pulsar IoT IDE, or copy `st7789_parallel.py` and
> `rgb565_display.py` into `/lib` on the microcontroller yourself.

## Connections

Nothing to wire: the LCD is built into the board. These are the fixed internal connections:

| Signal | GPIO |
| --- | ---: |
| Peripheral power | 15 |
| Backlight | 38 |
| LCD D0..D3 | 39, 40, 41, 42 |
| LCD D4..D7 | 45, 46, 47, 48 |
| Reset | 5 |
| Chip select | 6 |
| Data/command | 7 |
| Write | 8 |
| Read | 9 |

The first line of hardware setup drives GPIO 15 high. Do not remove it: it switches on the power
for the display, and the screen may stay black without it when the board runs from a battery.

## What happens

1. The screen turns dark blue and the logo appears at the top left, with a green **ONLINE** label
   whose status light glows up and down.
2. Three cards show temperature, humidity and battery. Their bars grow from nothing and then glide
   whenever a reading changes. The battery drains 1% every 2 seconds: its bar is green, turns
   yellow at 50% and red at 20%, then fills up again.
3. The temperature chart draws itself in from the right and keeps scrolling left, as a red line
   with the area underneath filled in.

The readings are made up; nothing is measured. The example is a picture of a user interface, to
show what the drawing methods can build. Put real sensor readings in `temperature`, `humidity` and
`battery` and it becomes a real dashboard.

## How it moves smoothly

- **Draw what never changes once.** `draw_once()` paints the background, logo, empty cards and
  labels a single time, before the loop.
- **Draw only what changed.** `card()` remembers what each card shows. A number is redrawn only
  when its text changes, straight over the old one: text and bitmaps on this display paint their
  own background, so nothing has to be cleared first, which would make it blink. A bar that grows
  only gets the new piece painted on the end.
- **Move the chart in memory.** The chart lives in a small `framebuf.FrameBuffer`, 308x54 pixels.
  Every frame, framebuf's `scroll()` slides it 2 pixels to the left, only those 2 new columns on
  the right are drawn, and the chart goes to the screen in one `blit_buffer`. The screen never
  shows half a frame, and the buffer is 33 KB rather than 109 KB for the whole screen. The chart's
  scale is fixed at 19 to 24 °C, because the part that has scrolled by cannot be redrawn at a new
  scale.
- **Keep a steady pace.** Each frame measures how long it took and sleeps for the rest of
  `frame_ms`, so the animation runs at the same speed whatever was redrawn.

framebuf keeps each colour's two bytes the other way round from the display, which is why the
chart's colours are swapped once, as `INK_...`. The driver's own `text` and `bitmap` do this for
you.

## The artwork

`pulsar_ui.py`, next to the script, is the same artwork as in the
[e-paper example](../spi-epaper-ssd1680): the logo on one line and large Poppins characters for the
numbers, as 1 bit bitmaps. They were made on a computer from the logo's SVG and the Poppins font,
because the board has neither. On this colour screen, `display.bitmap()` draws the 1 bits in one
colour and the 0 bits in another, so the black half of the logo is drawn in white here and its red
half in the brand red.

Any black and white image works the same way: turn it into `MONO_HLSB` bytes, 8 pixels a byte, and
pass them to `bitmap()` with a width, a height and two colours. The IDE copies `pulsar_ui.py` to the
board together with the script.

## Output

Once a second the script prints how many milliseconds the last frame took to draw. Anything under
`frame_ms`, 40, keeps the animation at 25 frames a second:
```
Frame: 23 ms
Frame: 22 ms
Frame: 27 ms
```

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Backlight and screen both stay off | GPIO 15 must go high before the display is set up |
| Backlight is on but the screen is blank | `st7789_parallel.py` is not in `/lib`; watch the REPL for an error |
| `ImportError: no module named 'pulsar_ui'` | `pulsar_ui.py` must be on the board next to the script |
| `MemoryError` | too little free memory for the 33 KB chart; reset the board, or run the script on its own |
| The picture is upside down | set `rotation = 3` instead of 1 |
| The layout is cut off or squashed | `rotation` is 0 or 2, which is portrait; use 1 or 3 |
| Red and blue are swapped | this is not the 1.9 inch T-Display-S3 |
| The animation is slow | the constructor needs `fast=True`, which only works with this board's LCD pins |

## Plotter

The only number printed is the frame time, so the plotter draws a line around 23 ms. Spikes are
frames where a number changed, or MicroPython pausing to free memory.

## Tested

- LilyGO T-Display-S3 running MicroPython 1.29.0: the driver's fast mode filled the full 320x170
  screen in 21 ms, blitted 100x100 pixels in 10 ms and drew a 17-character text line in 3 ms.
- Over 250 frames the animated dashboard took 22 to 37 ms a frame, 23.6 ms on average, so every
  frame fit in the 40 ms for 25 frames a second.
