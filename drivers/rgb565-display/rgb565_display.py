"""Drawing methods shared by RGB565 colour displays that draw straight to the panel.

A panel driver subclasses RGB565Display, sets ``width`` and ``height``, and provides three methods:

    _set_window(x0, y0, x1, y1)    select the inclusive area that the next pixels fill
    _write_pixels(buffer, width, height)  send a width x height big-endian RGB565 buffer into it
    _fill_pixels(color, count)     send one RGB565 colour count times into it

Everything here, from pixel() to text() and bitmap(), is built on those three, so a new panel only
has to know how to talk to its controller. No full-screen framebuffer is allocated.
"""

import framebuf
from micropython import const

BLACK = const(0x0000)
NAVY = const(0x000F)
BLUE = const(0x001F)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
RED = const(0xF800)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)


def color565(red, green=0, blue=0):
    """Return an RGB888 colour as the display's RGB565 integer."""
    if not isinstance(red, int):
        red, green, blue = red
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


def _swap(color):
    # framebuf stores RGB565 little-endian on the ESP32; swapping the colour's bytes makes its buffer
    # the big-endian stream the panel expects, so no per-pixel conversion is needed.
    return ((color & 0xFF) << 8) | (color >> 8)


class RGB565Display:
    width = 0
    height = 0

    def pixel(self, x, y, color):
        """Draw one RGB565 pixel. Coordinates outside the display are ignored."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self._set_window(x, y, x, y)
        self._fill_pixels(color, 1)

    def blit_buffer(self, buffer, x, y, width, height):
        """Draw a complete, big-endian RGB565 buffer at x, y."""
        if width <= 0 or height <= 0:
            return
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            raise ValueError("buffer must fit entirely inside the display")
        if len(buffer) != width * height * 2:
            raise ValueError("RGB565 buffer must contain width * height * 2 bytes")
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._write_pixels(buffer, width, height)

    def fill_rect(self, x, y, width, height, color):
        """Draw a clipped, filled RGB565 rectangle."""
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)
        if x0 >= x1 or y0 >= y1:
            return
        self._set_window(x0, y0, x1 - 1, y1 - 1)
        self._fill_pixels(color, (x1 - x0) * (y1 - y0))

    def fill(self, color):
        """Fill the whole display with one RGB565 colour."""
        self.fill_rect(0, 0, self.width, self.height, color)

    def hline(self, x, y, width, color):
        self.fill_rect(x, y, width, 1, color)

    def vline(self, x, y, height, color):
        self.fill_rect(x, y, 1, height, color)

    def rect(self, x, y, width, height, color, fill=False):
        """Draw a rectangle; pass fill=True for a filled rectangle."""
        if fill:
            self.fill_rect(x, y, width, height, color)
            return
        if width <= 0 or height <= 0:
            return
        self.hline(x, y, width, color)
        if height > 1:
            self.hline(x, y + height - 1, width, color)
        if height > 2:
            self.vline(x, y + 1, height - 2, color)
            if width > 1:
                self.vline(x + width - 1, y + 1, height - 2, color)

    def line(self, x0, y0, x1, y1, color):
        """Draw a one-pixel Bresenham line."""
        if x0 == x1 or y0 == y1:
            self.fill_rect(min(x0, x1), min(y0, y1), abs(x1 - x0) + 1, abs(y1 - y0) + 1, color)
            return
        # ponytail: diagonals are drawn pixel by pixel; batch runs into hlines if they get hot.
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def text(self, string, x, y, color=WHITE, background=BLACK):
        """Draw opaque text with MicroPython's built-in 8x8 pixel font."""
        if y < 0 or y + 8 > self.height or x >= self.width or not string:
            return
        if x < 0:
            raise ValueError("text x coordinate must not be negative")
        string = str(string)[: (self.width - x) // 8]
        if not string:
            return

        width = len(string) * 8
        pixels = bytearray(width * 16)
        glyphs = framebuf.FrameBuffer(pixels, width, 8, framebuf.RGB565)
        glyphs.fill(_swap(background))
        glyphs.text(string, 0, 0, _swap(color))
        self.blit_buffer(pixels, x, y, width, 8)

    def bitmap(self, data, x, y, width, height, color=WHITE, background=BLACK):
        """Draw a 1 bit image, such as a logo, with its top left corner at x, y.

        ``data`` is MONO_HLSB: 8 pixels a byte, a row at a time, the most significant bit on the
        left. 1 bits are drawn in ``color`` and 0 bits in ``background``. The image must fit.
        """
        pixels = bytearray(width * height * 2)
        palette = framebuf.FrameBuffer(bytearray(4), 2, 1, framebuf.RGB565)
        palette.pixel(0, 0, _swap(background))
        palette.pixel(1, 0, _swap(color))
        image = framebuf.FrameBuffer(bytearray(data), width, height, framebuf.MONO_HLSB)
        framebuf.FrameBuffer(pixels, width, height, framebuf.RGB565).blit(image, 0, 0, -1, palette)
        self.blit_buffer(pixels, x, y, width, height)
