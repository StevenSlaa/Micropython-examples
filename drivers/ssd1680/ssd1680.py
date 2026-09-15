# Driver for 2.9 inch 128x296 e-paper panels on the SSD1680 controller in black, white and red,
# such as the WeAct Studio 2.9 inch module.
#
# The command sequence follows GxEPD2's GxEPD2_290_C90c, the widely used Arduino driver for this
# panel: https://github.com/ZinggJM/GxEPD2
#
# The controller holds two images. In the black one a 1 bit is white and a 0 bit black; in the red
# one a 1 bit is red. Both are kept here as framebuffers in exactly that form, so drawing a colour
# means setting a bit in each.

import framebuf
from micropython import const
from time import sleep_ms, ticks_diff, ticks_ms

WHITE = const(0)
BLACK = const(1)
RED = const(2)

_SHORT = const(128)
_LONG = const(296)
_BYTES = const(4736)  # 128 * 296 / 8, one image
_PLANES = ((1, 0), (0, 0), (1, 1))  # (black image bit, red image bit) for WHITE, BLACK, RED


def _reverse(byte):
    result = 0
    for _ in range(8):
        result = (result << 1) | (byte & 1)
        byte >>= 1
    return result


_REVERSED = bytes(_reverse(byte) for byte in range(256))


class SSD1680:
    """A 2.9 inch SSD1680 e-paper panel on `spi`, with the Pin objects `cs`, `dc`, `rst` and `busy`.

    Draw in WHITE, BLACK or RED with the methods below, then call show(). `rotation` 90 and 270 are
    landscape (296 wide, 128 high), 0 and 180 portrait. `busy_timeout_ms` is how long the panel may
    stay busy before that is reported as a fault instead of waiting forever.
    """

    # A refresh measured 24 seconds at room temperature, and red takes longer in the cold, so the
    # timeout leaves plenty of room above that.
    def __init__(self, spi, cs, dc, rst, busy, rotation=270, busy_timeout_ms=60000):
        if rotation not in (0, 90, 180, 270):
            raise ValueError("rotation must be 0, 90, 180 or 270")
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        cs.init(cs.OUT, value=1)
        dc.init(dc.OUT, value=0)
        rst.init(rst.OUT, value=1)
        busy.init(busy.IN)
        self.rotation = rotation
        self.busy_timeout_ms = busy_timeout_ms
        landscape = rotation in (90, 270)
        self.width = _LONG if landscape else _SHORT
        self.height = _SHORT if landscape else _LONG
        # Landscape is kept as MONO_VLSB, a byte for every 8 rows of a column, because a column of
        # the landscape image is then 16 whole bytes of a panel row: rotating is copying bytes.
        mode = framebuf.MONO_VLSB if landscape else framebuf.MONO_HLSB
        self._black_buffer = bytearray(_BYTES)
        self._red_buffer = bytearray(_BYTES)
        self._black = framebuf.FrameBuffer(self._black_buffer, self.width, self.height, mode)
        self._red = framebuf.FrameBuffer(self._red_buffer, self.width, self.height, mode)
        self._out = bytearray(_BYTES)
        self.fill(WHITE)

    # Drawing. Everything is drawn into both images, with the bit each needs for the colour.

    def _both(self, color):
        if color not in (WHITE, BLACK, RED):
            raise ValueError("Use WHITE, BLACK or RED")
        black, red = _PLANES[color]
        return ((self._black, black), (self._red, red))

    def fill(self, color):
        for image, bit in self._both(color):
            image.fill(bit)

    def pixel(self, x, y, color):
        for image, bit in self._both(color):
            image.pixel(x, y, bit)

    def hline(self, x, y, width, color):
        for image, bit in self._both(color):
            image.hline(x, y, width, bit)

    def vline(self, x, y, height, color):
        for image, bit in self._both(color):
            image.vline(x, y, height, bit)

    def line(self, x1, y1, x2, y2, color):
        for image, bit in self._both(color):
            image.line(x1, y1, x2, y2, bit)

    def rect(self, x, y, width, height, color, fill=False):
        for image, bit in self._both(color):
            if fill:
                image.fill_rect(x, y, width, height, bit)
            else:
                image.rect(x, y, width, height, bit)

    def ellipse(self, x, y, x_radius, y_radius, color, fill=False):
        for image, bit in self._both(color):
            image.ellipse(x, y, x_radius, y_radius, bit, fill)

    def text(self, string, x, y, color=BLACK, scale=1):
        """Draws `string` in the built-in 8x8 pixel font, `scale` times as large."""
        if scale == 1:
            for image, bit in self._both(color):
                image.text(string, x, y, bit)
            return
        if not string:
            return
        width = 8 * len(string)
        glyphs = framebuf.FrameBuffer(bytearray((width + 7) // 8 * 8), width, 8, framebuf.MONO_HLSB)
        glyphs.text(string, 0, 0, 1)
        for glyph_y in range(8):
            for glyph_x in range(width):
                if glyphs.pixel(glyph_x, glyph_y):
                    self.rect(x + glyph_x * scale, y + glyph_y * scale, scale, scale, color, True)

    def bitmap(self, data, x, y, width, height, color=BLACK):
        """Draws a 1 bit image, such as a logo, with its top left corner at x, y.

        `data` is MONO_HLSB: 8 pixels a byte, a row at a time, the most significant bit on the left.
        1 bits are drawn in `color`; 0 bits leave the screen as it was.
        """
        images = self._both(color)
        row_bytes = (width + 7) // 8
        for row in range(height):
            offset = row * row_bytes
            for column in range(width):
                if data[offset + column // 8] & (0x80 >> (column & 7)):
                    for image, bit in images:
                        image.pixel(x + column, y + row, bit)

    # Talking to the panel.

    def _native(self, buffer):
        """An image in the panel's own layout: portrait, MONO_HLSB, row 0 first."""
        rotation, out = self.rotation, self._out
        if rotation == 0:
            return buffer
        if rotation == 180:
            for index in range(_BYTES):
                out[index] = _REVERSED[buffer[_BYTES - 1 - index]]
            return out
        # Landscape (x, y) is panel (127 - y, x) at 90 and (y, 295 - x) at 270. Panel row n is
        # landscape column n or 295 - n, and its 16 bytes are that column's 16 bytes of 8 rows:
        # in reverse order at 90, bit reversed at 270.
        index = 0
        for row in range(_LONG):
            if rotation == 90:
                for band in range(15, -1, -1):
                    out[index] = buffer[band * _LONG + row]
                    index += 1
            else:
                column = _LONG - 1 - row
                for band in range(16):
                    out[index] = _REVERSED[buffer[band * _LONG + column]]
                    index += 1
        return out

    def _command(self, command, data=None):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes((command,)))
        if data is not None:
            self.dc.value(1)
            self.spi.write(data)
        self.cs.value(1)

    def _wait(self, step):
        start = ticks_ms()
        while self.busy.value():
            if ticks_diff(ticks_ms(), start) > self.busy_timeout_ms:
                raise OSError(
                    "The e-paper stayed busy for %d ms during %s: check the BUSY, RES and power wires"
                    % (self.busy_timeout_ms, step)
                )
            sleep_ms(10)

    def show(self):
        """Puts the drawing on the panel. Takes about 25 seconds, and the screen flashes: normal."""
        # Every refresh starts from a hardware reset and ends in deep sleep. A glitch, a brown-out or
        # an interrupted refresh cannot leave the controller in a state the next one inherits, and
        # the panel is never left with its high voltage on, which wears it out.
        self.rst.value(0)
        sleep_ms(10)
        self.rst.value(1)
        sleep_ms(10)
        self._wait("reset")
        self._command(0x12)  # software reset
        sleep_ms(10)
        self._wait("software reset")
        self._command(0x01, b"\x27\x01\x00")  # driver output control: 296 gate lines
        self._command(0x11, b"\x03")  # data entry: x and y count up
        self._command(0x3C, b"\x05")  # border waveform
        self._command(0x18, b"\x80")  # use the internal temperature sensor
        self._command(0x21, b"\x00\x80")  # display update control
        self._command(0x44, b"\x00\x0f")  # RAM columns: bytes 0 to 15
        self._command(0x45, b"\x00\x00\x27\x01")  # RAM rows: 0 to 295
        self._command(0x4E, b"\x00")  # start at column 0
        self._command(0x4F, b"\x00\x00")  # and row 0
        self._command(0x24, self._native(self._black_buffer))
        self._command(0x26, self._native(self._red_buffer))
        self._command(0x22, b"\xf7")  # full refresh, then switch the high voltage off
        self._command(0x20)
        self._wait("refresh")
        self._command(0x10, b"\x01")  # deep sleep, until the next show() resets it
