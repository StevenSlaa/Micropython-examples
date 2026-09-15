---
driver: rgb565-display
author: Steven Slaa
---

# RGB565 display drawing (shared)

The drawing methods that colour display drivers in this library have in common. On its own it
draws nothing: a panel driver such as [st7789-parallel](../st7789-parallel) or
[axs15231b](../axs15231b) builds on it, and you use that driver's display object.

## Install

Install it from the Pulsar IoT library panel, or copy `rgb565_display.py` to `/lib` on the board,
next to the panel driver that needs it. Examples that use a colour display list it in their
requirements, so the IDE installs it for you.

## What every display gets

| Method | What it draws |
| --- | --- |
| `pixel(x, y, color)` | one pixel |
| `fill(color)` | the whole screen |
| `fill_rect(x, y, width, height, color)` | a filled rectangle, clipped to the screen |
| `rect(x, y, width, height, color, fill=False)` | a rectangle outline, or filled |
| `hline(x, y, width, color)`, `vline(x, y, height, color)` | straight lines |
| `line(x0, y0, x1, y1, color)` | any line |
| `text(string, x, y, color, background)` | 8x8 text with MicroPython's built-in font |
| `bitmap(data, x, y, width, height, color, background)` | a 1 bit `MONO_HLSB` image, such as a logo |
| `blit_buffer(buffer, x, y, width, height)` | an RGB565 buffer, high byte first, such as a `framebuf` sprite |

Colours are RGB565 integers. `color565(red, green, blue)` turns 0-255 values into one, and
`BLACK`, `NAVY`, `BLUE`, `GREEN`, `CYAN`, `RED`, `MAGENTA`, `YELLOW` and `WHITE` are ready to use.
Every panel driver re-exports these, so `from axs15231b import WHITE` works.

Drawing goes straight to the panel; there is no full-screen framebuffer and no `show()`.

## Writing a driver for another panel

Subclass `RGB565Display`, set `width` and `height`, and provide three methods that talk to your
controller:

```python
from rgb565_display import RGB565Display

class MyPanel(RGB565Display):
    def _set_window(self, x0, y0, x1, y1):
        ...  # select the area, corners included, that the next pixels fill

    def _write_pixels(self, buffer, width, height):
        ...  # send a width x height buffer of big-endian RGB565

    def _fill_pixels(self, color, count):
        ...  # send one colour count times
```

Every drawing method above is built on those three.
