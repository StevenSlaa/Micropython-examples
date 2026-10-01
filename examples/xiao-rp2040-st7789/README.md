---
example: xiao-rp2040-st7789
author: Steven Slaa
---

# XIAO RP2040 + ST7789 (240x240 colour display)

Drives a 240x240 ST7789 colour display from a Seeed XIAO RP2040. It loops through four scenes:

1. A title card on a rainbow gradient.
2. A spinning 3D cube, with its frame rate in the corner.
3. A warp-speed starfield.
4. A zoom into the Mandelbrot set, ending in colour cycling.

The animations are drawn into a 112KB framebuf in RAM and sent to the display in one blit.
Drawing through the driver pixel by pixel costs an SPI transaction per pixel and is far too
slow to animate.

## How it gets its speed

| | Before | After |
| --- | --- | --- |
| Full screen blit | 46ms | 22ms |
| Cube | not measured | 27 fps |
| Starfield | 7 fps | 30 fps |
| Mandelbrot | ~10s, drawn once | zoom at ~11 fps |

- **CPU at 200MHz**, the RP2040's rated maximum, instead of 125MHz.
- **SPI at 50MHz.** MicroPython leaves the RP2040's peripheral clock at 48MHz, which caps SPI at
  24MHz whatever baudrate you ask for. The demo switches the peripheral clock to the CPU clock
  with one register write. The UART also runs from that clock, so its baudrates are wrong
  afterwards; nothing here uses it (the REPL is on USB).
- **Viper on both cores** for the Mandelbrot: fixed-point maths compiled to machine code, with
  each core taking alternate rows.
- **`@micropython.native`** for the star loop, and the colours worked out once, not per star.
- **Motion follows the clock, not the frame count**, so a slow frame does not make it stutter.

## Requires
This example needs the [ST7789 display](../../drivers/st7789py) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| ST7789 | XIAO | GPIO |
| --- | --- | --- |
| VCC | 3V3 | |
| GND | GND | |
| SCL / SCK | D8 | GP2 |
| SDA / MOSI | D10 | GP3 |
| DC | D0 | GP26 |
| RES | D1 | GP27 |
| CS | D2 | GP28 |
| BL | D3 | GP29 |

SCK and MOSI must be on these pins: they are the XIAO's hardware SPI0. The rest can move.

## Troubleshooting

- **Noise or wrong colours**: 50MHz is too fast for your wiring. Set `spi_divider = 6` (33MHz)
  or `8` (25MHz).
- **Backlight on, nothing drawn**: wrong SPI mode. With CS, use `polarity=0, phase=0` (the
  default here); `polarity=1, phase=0` leaves the screen blank.
- **No CS pin on your module**: set `cs_pin = None` and use `polarity=1, phase=1`.
- **Colours inverted (black background shows white)**: call `display.inversion_mode(False)`
  after creating the display. Most 240x240 panels need inversion on, which the driver sets.
- **`MemoryError`**: the screen buffer needs 112KB in one piece. Do not import the driver's
  `vga2_16x32` font as well; it takes 67KB.
