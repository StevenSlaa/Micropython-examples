---
driver: axs15231b
author: Steven Slaa
---

# AXS15231B QSPI display and touch

Driver for the 3.4 inch, 180x640 colour touch display of the LilyGO T-Display-S3 Long. Its
AXS15231B chip runs both the picture and the capacitive touch: the picture over a QSPI bus, the
touch over I2C.

MicroPython has no QSPI bus, so the driver clocks it out itself, with Viper-compiled writes straight
to the ESP32-S3's GPIO register. That is fast enough for animation: a full-screen fill takes about
58 ms. The drawing methods (`fill_rect`, `text`, `bitmap`, `blit_buffer` and the rest) come from
the shared [rgb565-display](../rgb565-display) driver, the same ones the
[st7789-parallel](../st7789-parallel) driver uses.

## Install

Install it from the Pulsar IoT library panel, or copy `axs15231b.py` and `rgb565_display.py` into
`/lib` on the board.

## Usage

The pins are fixed by the board, so there are none to pass:

```python
from machine import I2C, Pin
from axs15231b import AXS15231B, AXS15231BTouch, BLACK, WHITE, RED

display = AXS15231B(rotation=1)  # 640x180 landscape, USB port on the right
touch = AXS15231BTouch(I2C(0, scl=Pin(10), sda=Pin(15), freq=400000), rotation=1)

display.fill(BLACK)
display.text("Hello!", 10, 10, WHITE, BLACK)

while True:
    point = touch.read()
    if point:
        display.fill_rect(point[0] - 2, point[1] - 2, 5, 5, RED)
```

| Rotation | Size | Holding the board |
| --- | --- | --- |
| 0 | 180x640 | portrait, USB port at the bottom |
| 1 | 640x180 | landscape, USB port on the right |
| 2 | 180x640 | portrait, USB port at the top |
| 3 | 640x180 | landscape, USB port on the left |

The panel cannot rotate its own picture (its orientation setting mirrors or garbles it), so the
driver rotates every drawing itself. Change it later with `display.rotation(r)`, and give the
touch the same value, `touch.rotation = r`, so touches arrive in the coordinates you draw with.

## Touch

`touch.read()` returns `(x, y)` while a finger is down and `None` otherwise. Call it every frame of
your loop: the chip hands out each touch report only once, and a tap is the moment `read()` goes
from `None` to a point.

Two things about this chip that the driver takes care of:

- Between reports it answers with garbled frames, or repeats the last report. The driver recognises
  a real report by its counter and ignores the rest, so they never show up as extra touches.
- A finger that rests without moving sends no reports at all. The driver keeps it pressed until
  the chip reports it lifted.

`calibration=(left, right, top, bottom)` holds the raw readings at the edges of the portrait screen,
measured on a T-Display-S3 Long. Tracing a finger along an edge draws a line a few millimetres
inside it: that is where the centre of your fingertip is, not a calibration error.

## Pin map

| Signal | GPIO |
| --- | ---: |
| QSPI CS | 12 |
| QSPI clock | 17 |
| QSPI D0, D1, D2, D3 | 13, 18, 21, 14 |
| Display and touch reset | 16 |
| Backlight | 1 |
| Touch I2C SDA, SCL | 15, 10 |
| Touch interrupt (unused) | 11 |

The QSPI pins are built into the Viper code. Another board with an AXS15231B on different pins
needs new register masks in `axs15231b.py`.

## Speed and memory

Measured on a T-Display-S3 Long with MicroPython 1.29.0:

| Operation | Time |
| --- | ---: |
| Setting up the display | 632 ms |
| Full-screen fill | 58 ms |
| A line of text | 3 to 5 ms |
| `touch.read()` | under 2 ms |

Two quirks of the panel cost a little speed. It garbles a drawing area that is exactly one of its
columns wide but several rows tall (a 1 pixel horizontal line in landscape), and a wider area that
starts on column 3, 7, 11 and so on. Both were found by testing, not in a datasheet. The driver
sends the first column of such an area a pixel at a time and the rest normally, so the picture is
right, but something drawn on those columns takes longer. Keep those draws out of fast animation.

There is no full-screen framebuffer: 640x180 in RGB565 would take 230 KB, more than the free memory
of a standard ESP32-S3 build. Drawing goes straight to the panel. For something that changes a lot,
draw it into a small `framebuf.FrameBuffer` and send that with `blit_buffer`, as the example does
with its chart.

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Backlight on, no picture | the drivers are missing from `/lib`, or another program left the panel in a bad state: press RST |
| `ValueError: this driver writes ESP32-S3 GPIO registers` | this is not an ESP32-S3 |
| Touches land a little inside the edges | normal for a fingertip; see Touch above |
| The board freezes while running, with no battery connected | the board's SY6970 battery charger keeps trying to charge: switch its watchdog and charging off, as the [example](../../examples/t-display-s3-long) does |
| The board stops answering over USB after sitting unused, while the picture stays | press RST; seen during testing, cause not found |

## Credits

The protocol, pin map and touch report format come from LilyGO's
[T-Display-S3-Long repository](https://github.com/Xinyuan-LilyGO/T-Display-S3-Long) (the `master`
branch, for boards with the AXS15231B's own touch). Newer boards with a separate CST3530 touch chip
are not supported by this driver's touch class.
