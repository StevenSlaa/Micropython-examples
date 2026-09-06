---
driver: pixels
author: Steven Slaa
---

# Addressable LEDs (WS2812B / SK6812)

MicroPython already ships the wire protocol: `neopixel` is frozen into the ESP32 and RP2
firmware, and `bpp=4` drives SK6812 RGBW strips. This driver is the layer on top that firmware
does not give you — live brightness, gamma correction, HSV, and the RGBW white channel.

If all you need is to set raw pixel values, skip this driver and use `neopixel` directly.

## Install

Install it from the Pulsar IoT library panel, or copy `pixels.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from pixels import Pixels, hsv

strip = Pixels(Pin(5), 30, brightness=0.3)   # WS2812B, 30 LEDs

strip.fill((0, 0, 0))
strip[0] = (255, 0, 0)
strip[1] = hsv(0.33)                          # hue 0..1 around the wheel
strip.write()                                 # nothing lights up until write()
```

A rainbow that stays smooth at low brightness, because gamma is applied on write:

```python
for frame in range(256):
    for i in range(len(strip)):
        strip[i] = hsv((i / len(strip) + frame / 256) % 1.0)
    strip.write()
```

SK6812 RGBW, with the white LED driven from the colour you set:

```python
strip = Pixels(Pin(5), 30, bpp=4, auto_white=True)
strip[0] = (255, 200, 150)   # warm white, mostly through the white LED
strip[1] = (0, 0, 0, 255)    # or address the white channel yourself
```

## Notes

- `bpp=3` is WS2812B, WS2812 and WS2811 (GRB). `bpp=4` is SK6812 RGBW (GRBW).
- Colours you set are stored unchanged; `brightness` and `gamma` are applied in `write()`, so
  changing either takes effect across the whole strip on the next write.
- `brightness` is 0..1 and matters: a strip at full brightness draws about 60mA per LED, which
  is more than a USB port gives you past roughly a dozen LEDs. Power long strips separately and
  share the ground with the board.
- `gamma` defaults to 2.6, which is about right for these LEDs. Lower it towards 1.0 if fades
  look too dark in the middle, raise it if they wash out. Pass `gamma=1.0` to disable it.
- `auto_white=True` folds the part shared by red, green and blue into the white LED: cleaner
  whites and less current, but some strips shift hue doing it, so it is off by default.
- `timing` is passed through to `neopixel`: `1` for 800kHz (nearly all strips), `0` for 400kHz
  WS2811, or a `(high_0, low_0, high_1, low_1)` nanosecond tuple for a strip that needs coaxing.
- `write()` is a per-pixel Python loop, a few milliseconds for a couple of hundred LEDs. Long
  strips at a high frame rate want a PIO or RMT driver instead.
- The level shifting matters more than the code: a 3.3V data line into a 5V strip works often
  enough to be a trap. If the first LED flickers, add a level shifter, a 300–500Ω series
  resistor on data, and a 1000µF capacitor across the strip supply.

## Tests

`python3 -B drivers/pixels/test_pixels.py` checks the colour maths off-board. It stubs `neopixel`,
so it needs no hardware and is not installed to the board.
