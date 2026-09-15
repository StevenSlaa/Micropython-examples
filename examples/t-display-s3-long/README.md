---
example: t-display-s3-long
author: Steven Slaa
---

# LilyGO T-Display S3 Long (3.4 inch touch LCD)

In this example the LilyGO T-Display-S3 Long draws an illustrative, animated dashboard on its
built-in 640x180 touch display: the Pulsar IoT logo, three cards with readings and a live chart.
Tap a card and the chart switches to that reading.

The display is an AXS15231B on a QSPI bus, a chip that also runs the capacitive touch. MicroPython
has no QSPI bus, so the driver clocks it out itself, fast enough to animate the screen at about 16
frames a second. The [driver README](../../drivers/axs15231b) explains more.

## Requires

This example needs three drivers installed on the board:

- [AXS15231B QSPI display and touch](../../drivers/axs15231b), which talks to the display and touch
- [RGB565 display drawing (shared)](../../drivers/rgb565-display), with the drawing methods
- [SY6970 battery charger](../../drivers/sy6970), for the board's charger chip

> Install them from the library panel in the Pulsar IoT IDE, or copy `axs15231b.py`,
> `rgb565_display.py` and `sy6970.py` into `/lib` on the microcontroller yourself.

## Connections

Nothing to wire: the display and touch are built into the board, on fixed pins.

| Signal | GPIO |
| --- | ---: |
| Display QSPI CS, clock | 12, 17 |
| Display QSPI D0, D1, D2, D3 | 13, 18, 21, 14 |
| Display and touch reset | 16 |
| Backlight | 1 |
| Touch I2C SDA, SCL | 15, 10 |

This is the version of the board whose touch is part of the AXS15231B, at I2C address 0x3B. Newer
boards with a separate CST3530 touch chip draw the dashboard, but do not react to taps.

## The battery charger

The board has a battery charger chip, an SY6970, on the same I2C bus as the touch. Left alone, it
resets its own settings every 40 seconds and keeps trying to charge, even when no battery is
connected. The script sets it up with the [SY6970 driver](../../drivers/sy6970): the driver switches the
watchdog off, and with `battery = False` the script switches charging off too. Plug in a LiPo? Set `battery = True`, so it charges.

On the tested board, with no battery and charging left on, the dashboard froze after about two
minutes; with charging off it ran for 8.3 minutes. The board did still stop answering over USB a
few times while it sat unused between runs. Press RST when that happens.

## What happens

Hold the board sideways with the USB port on the right.

1. The logo appears at the top left and a green **ONLINE** label at the top right, with a status
   light that glows up and down.
2. Three cards show temperature, humidity and battery, each with its lowest and highest value so
   far and a bar that glides to its new length. The battery bar is green, turns yellow at 50% and
   red at 20%, then fills up again.
3. On the right, a chart of the selected card draws itself in and keeps scrolling left. The selected
   card has a red outline.
4. Tap another card: the outline moves there and the chart starts again with that reading.

The readings are made up; nothing is measured. Put real sensor values into `temperature`,
`humidity` and `battery` and it becomes a real dashboard.

## How it works

- **Draw what never changes once.** `draw_once()` paints the background, header and empty cards a
  single time.
- **Draw only what changed.** `card()` remembers what each card shows. A number is redrawn only when
  its text changes, straight over the old one, and a bar only gets its new piece painted on.
- **Move the chart in memory.** The chart is a 296x120 `framebuf.FrameBuffer`. Each frame it slides
  2 pixels left with `scroll()`, only the newest columns are drawn, and the whole chart goes to the
  screen in one `blit_buffer`, so it never shows half a frame. That blit is most of each frame's work.
- **A tap is the moment a finger comes down.** `touch.read()` returns a point while a finger is on
  the screen and `None` otherwise. The loop reads it every frame and only reacts when it goes from
  `None` to a point, so holding a finger on a card does not keep switching it.
- **Keep a steady pace.** Each frame sleeps for whatever is left of `frame_ms`, 60 ms.

framebuf keeps a colour's two bytes the other way round from the display, which is why the chart's
colours are swapped once, as `INK_...`. The driver's own drawing methods do this for you.

## The artwork

`pulsar_ui.py`, next to the script, is the same artwork as in the
[e-paper example](../spi-epaper-ssd1680): the logo and large Poppins characters for the numbers, as
1 bit bitmaps. The logo's 1 bit swirl icon was made for e-paper and looks like broken lines on this
sharp screen, so this copy of `pulsar_ui.py` also holds `ICON`: the Pulsar IoT icon as a smooth
24x24 colour picture, made from the icon's PNG and blended onto the dashboard's background colour.
The script draws it over the swirl with `blit_buffer`, and keeps the lettering.

## Output

Every 16 frames the script prints how long the last frame took to draw:
```
Frame: 57 ms
Frame: 58 ms
Frame: 56 ms
```

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Backlight on, no picture | the drivers are not in `/lib`; watch the REPL for an error |
| `ImportError: no module named 'pulsar_ui'` | `pulsar_ui.py` must be on the board next to the script |
| The picture is upside down | set `rotation = 3` and hold the board with USB on the left |
| Taps land a little inside the edges | normal: that is where the centre of your fingertip is |
| Taps do nothing | a newer board with a CST3530 touch chip; the display still works |
| The board freezes while running | `battery = True` without a battery connected: set it to `False` |
| The board stops answering over USB after sitting unused | press RST; seen during testing, cause not found |
| `MemoryError` | too little free memory for the 71 KB chart; reset the board and run the script on its own |

## Plotter

The only number printed is the frame time, so the plotter draws a line around 57 ms. A tap gives
one spike of about 250 ms, while the card outlines are redrawn.

## Tested

- LilyGO T-Display-S3 Long with AXS15231B touch, running MicroPython 1.29.0. Frames took 56 to 59 ms,
  a tap redrew the outlines in about 250 ms, 10 taps out of 10 registered, and 137 KB of memory was
  free while the dashboard ran.
- With the charger left as it starts up and no battery connected, the board froze after about two
  minutes. With charging switched off, the dashboard ran for 8.3 minutes without a problem.
