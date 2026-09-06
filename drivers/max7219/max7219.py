"""
MicroPython max7219 cascadable 8x8 LED matrix driver
https://github.com/mcauser/micropython-max7219

Changed for this catalog: the `reverse` and `transpose` options below, for the 4-in-1 boards
whose modules are wired in the other order or with rows and columns swapped.

MIT License
Copyright (c) 2017 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from micropython import const
import framebuf

_NOOP = const(0)
_DIGIT0 = const(1)
_DECODEMODE = const(9)
_INTENSITY = const(10)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)

class Matrix8x8:
    """Driver for cascading MAX7219 8x8 LED matrices.

    `num` is how many 8x8 modules are chained, so a 4-in-1 board is 4 and gives a 32x8 display.

    The two flags are for the cheap boards. If the display works but reads back to front, set
    `reverse=True`; if the characters lie on their side, set `transpose=True`. There is no way
    to ask the board which it is, so try them.

    >>> from machine import Pin, SPI
    >>> import max7219
    >>> spi = SPI(1, baudrate=10000000, polarity=1, phase=0, sck=Pin(14), mosi=Pin(13))
    >>> display = max7219.Matrix8x8(spi, Pin(15), 4)
    >>> display.text('Hi', 0, 0, 1)
    >>> display.show()
    """

    def __init__(self, spi, cs, num, reverse=False, transpose=False):
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, True)
        self.buffer = bytearray(8 * num)
        self.num = num
        self.reverse = reverse
        self.transpose = transpose
        fb = framebuf.FrameBuffer(self.buffer, 8 * num, 8, framebuf.MONO_HLSB)
        self.framebuf = fb
        # Provide methods for accessing FrameBuffer graphics primitives. This is a workround
        # because inheritance from a native class is currently unsupported.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        self.fill = fb.fill  # (col)
        self.pixel = fb.pixel  # (x, y[, c])
        self.hline = fb.hline  # (x, y, w, col)
        self.vline = fb.vline  # (x, y, h, col)
        self.line = fb.line  # (x1, y1, x2, y2, col)
        self.rect = fb.rect  # (x, y, w, h, col)
        self.fill_rect = fb.fill_rect  # (x, y, w, h, col)
        self.text = fb.text  # (string, x, y, col=1)
        self.scroll = fb.scroll  # (dx, dy)
        self.blit = fb.blit  # (fbuf, x, y[, key])
        self.init()

    def _write(self, command, data):
        self.cs(0)
        for m in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init(self):
        for command, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self._write(command, data)

    def brightness(self, value):
        """0 is dimmest and 15 brightest. All the modules in the chain change together."""
        if not 0 <= value <= 15:
            raise ValueError("Brightness out of range")
        self._write(_INTENSITY, value)

    def _transposed(self):
        """The frame buffer with each 8x8 block's rows and columns swapped.

        Some 4-in-1 boards wire each module's rows to the driver's columns, which shows up as
        every character lying on its side.
        """
        # ponytail: 64 bit tests per module in Python, a few milliseconds for a 4 module chain.
        # Only runs when transpose is on; a viewport-sized bytearray shuffle would be faster.
        out = bytearray(len(self.buffer))
        for m in range(self.num):
            for y in range(8):
                row = 0
                for x in range(8):
                    if self.buffer[(x * self.num) + m] & (1 << (7 - y)):
                        row |= 1 << (7 - x)
                out[(y * self.num) + m] = row
        return out

    def show(self):
        """Pushes the frame buffer to the display. Nothing appears until this is called."""
        buffer = self._transposed() if self.transpose else self.buffer
        for y in range(8):
            self.cs(0)
            for m in range(self.num):
                module = self.num - 1 - m if self.reverse else m
                self.spi.write(bytearray([_DIGIT0 + y, buffer[(y * self.num) + module]]))
            self.cs(1)
