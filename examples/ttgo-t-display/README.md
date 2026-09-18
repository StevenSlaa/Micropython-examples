---
example: ttgo-t-display
author: Steven Slaa
---

# TTGO T-Display v1.1 (1.14 inch SPI LCD)

In this example the LilyGO/TTGO T-Display v1.1 (the original ESP32 board, not the S3) shows text
on its built-in 1.14 inch colour LCD and counts presses of its two buttons.

The display is a 135x240 ST7789V on SPI. The [st7789py](../../drivers/st7789py) driver already
supports this size: pass `135, 240` and it applies the panel's offsets and colour inversion itself.

## Requires
This example needs the [ST7789 display](../../drivers/st7789py) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy `st7789py.py` and
> `vga2_16x32.py` into `/lib` on the microcontroller yourself.

## Connections

Nothing to wire: the LCD and buttons are built into the board.

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

## Output
```
Left: 0 Right: 0
Left: 1 Right: 0
Left: 1 Right: 1
```

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| Picture is upside down | set `rotation = 3` instead of 1 |
| Text is cut off | `rotation` is 0 or 2 (portrait); use 1 or 3 |
| Picture is shifted by a few pixels | a different board revision; adjust `WIDTH_135` in `st7789py.py` |
