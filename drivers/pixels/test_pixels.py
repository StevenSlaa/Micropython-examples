# Run with: python3 -B drivers/pixels/test_pixels.py
# Stubs the firmware's neopixel module so the colour maths can be checked off-board.
import sys, types


class _NeoPixel:
    ORDER = (1, 0, 2, 3)

    def __init__(self, pin, n, bpp=3, timing=1):
        self.n, self.bpp, self.buf = n, bpp, bytearray(n * bpp)

    def __setitem__(self, i, v):
        for channel in range(self.bpp):
            self.buf[i * self.bpp + self.ORDER[channel]] = v[channel]

    def write(self):
        self.written = bytes(self.buf)


sys.modules["neopixel"] = types.SimpleNamespace(NeoPixel=_NeoPixel)
from pixels import Pixels, gamma_table, hsv  # noqa: E402

assert hsv(0.0) == (255, 0, 0), hsv(0.0)
assert hsv(1 / 3) == (0, 255, 0), hsv(1 / 3)
assert hsv(2 / 3) == (0, 0, 255), hsv(2 / 3)
assert hsv(1.0) == hsv(0.0), "hue wraps"
assert hsv(0.0, saturation=0.0) == (255, 255, 255), "no saturation is white"

table = gamma_table()
assert table[0] == 0 and table[255] == 255, "the ends are not clipped"
assert all(table[i] <= table[i + 1] for i in range(255)), "gamma is monotonic"
assert gamma_table(brightness=0.5)[255] == 128, "brightness scales the top"

strip = Pixels(None, 4, gamma=1.0)
strip[0] = (255, 128, 0)
assert strip[0] == (255, 128, 0), "colours are stored unmodified"
strip.fill((10, 20, 30))
assert strip[3] == (10, 20, 30) and strip[-1] == (10, 20, 30), "fill covers the strip"
strip.write()
assert strip._strip.written[:3] == bytes((20, 10, 30)), "written in GRB order"
strip.brightness = 0.5
strip.write()
assert strip._strip.written[:3] == bytes((10, 5, 15)), "brightness applies on write"

rgbw = Pixels(None, 1, bpp=4, gamma=1.0, auto_white=True)
rgbw[0] = (200, 255, 200)
assert rgbw[0] == (0, 55, 0, 200), "the shared channel moves to white"
rgbw.auto_white = False
rgbw[0] = (200, 255, 200)
assert rgbw[0] == (200, 255, 200, 0), "without auto_white the white LED stays off"
rgbw[0] = (1, 2, 3, 4)
assert rgbw[0] == (1, 2, 3, 4), "an explicit white channel passes through"

print("pixels: ok")
