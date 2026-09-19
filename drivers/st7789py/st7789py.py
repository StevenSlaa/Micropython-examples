"""
Copyright (c) 2020, 2021 Russ Hughes

This file incorporates work covered by the following copyright and
permission notice and is licensed under the same terms:

The MIT License (MIT)

Copyright (c) 2019 Ivan Belokobylskiy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

The driver is based on devbis' st7789py_mpy module from
https://github.com/devbis/st7789py_mpy.

This driver adds support for:

- 320x240, 240x240 and 135x240 pixel displays
- Display rotation
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing text using converted TrueType fonts.
- Drawing converted bitmaps

"""

import time
from micropython import const
import ustruct as struct

# commands
ST7789_NOP = const(0x00)
ST7789_SWRESET = const(0x01)
ST7789_RDDID = const(0x04)
ST7789_RDDST = const(0x09)

ST7789_SLPIN = const(0x10)
ST7789_SLPOUT = const(0x11)
ST7789_PTLON = const(0x12)
ST7789_NORON = const(0x13)

ST7789_INVOFF = const(0x20)
ST7789_INVON = const(0x21)
ST7789_DISPOFF = const(0x28)
ST7789_DISPON = const(0x29)
ST7789_CASET = const(0x2A)
ST7789_RASET = const(0x2B)
ST7789_RAMWR = const(0x2C)
ST7789_RAMRD = const(0x2E)

ST7789_PTLAR = const(0x30)
ST7789_VSCRDEF = const(0x33)
ST7789_COLMOD = const(0x3A)
ST7789_MADCTL = const(0x36)
ST7789_VSCSAD = const(0x37)

ST7789_MADCTL_MY = const(0x80)
ST7789_MADCTL_MX = const(0x40)
ST7789_MADCTL_MV = const(0x20)
ST7789_MADCTL_ML = const(0x10)
ST7789_MADCTL_BGR = const(0x08)
ST7789_MADCTL_MH = const(0x04)
ST7789_MADCTL_RGB = const(0x00)

ST7789_RDID1 = const(0xDA)
ST7789_RDID2 = const(0xDB)
ST7789_RDID3 = const(0xDC)
ST7789_RDID4 = const(0xDD)

COLOR_MODE_65K = const(0x50)
COLOR_MODE_262K = const(0x60)
COLOR_MODE_12BIT = const(0x03)
COLOR_MODE_16BIT = const(0x05)
COLOR_MODE_18BIT = const(0x06)
COLOR_MODE_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = ">H"
_ENCODE_POS = ">HH"
_DECODE_PIXEL = ">BBB"

# Pixels per SPI transfer when filling. Bigger is faster, but only up to
# about this size: the transfer itself then outweighs the Python overhead.
_BUFFER_SIZE = const(1024)

# Characters kept as ready made pixels, and colour pairs kept as lookup
# tables to build them with; see _glyph(). A 16x32 character costs 1KB and a
# table 4KB, so both are capped.
_GLYPH_CACHE = const(16)
_LUT_CACHE = const(4)

# Rotation tables (width, height, xstart, ystart)[rotation % 4]

WIDTH_320 = [(240, 320,  0,  0),
             (320, 240,  0,  0),
             (240, 320,  0,  0),
             (320, 240,  0,  0)]

WIDTH_240 = [(240, 240,  0,  0),
             (240, 240,  0,  0),
             (240, 240,  0, 80),
             (240, 240, 80,  0)]

WIDTH_135 = [(135, 240, 52, 40),
             (240, 135, 40, 53),
             (135, 240, 53, 40),
             (240, 135, 40, 52)]

# MADCTL ROTATIONS[rotation % 4]
ROTATIONS = [0x00, 0x60, 0xc0, 0xa0]


def color565(red, green=0, blue=0):
    """
    Convert red, green and blue values (0-255) into a 16-bit 565 encoding.
    """
    try:
        red, green, blue = red  # see if the first var is a tuple/list
    except TypeError:
        pass
    return (red & 0xf8) << 8 | (green & 0xfc) << 3 | blue >> 3


def _encode_pos(x, y):
    """Encode a postion into bytes."""
    return struct.pack(_ENCODE_POS, x, y)


def _encode_pixel(color):
    """Encode a pixel color into bytes."""
    return struct.pack(_ENCODE_PIXEL, color)


class ST7789():
    """
    ST7789 driver class

    Args:
        spi (spi): spi object **Required**
        width (int): display width **Required**
        height (int): display height **Required**
        reset (pin): reset pin
        dc (pin): dc pin **Required**
        cs (pin): cs pin
        backlight(pin): backlight pin
        rotation (int): display rotation
            - 0-Portrait
            - 1-Landscape
            - 2-Inverted Portrait
            - 3-Inverted Landscape
    """
    def __init__(self, spi, width, height, reset=None, dc=None,
                 cs=None, backlight=None, rotation=0):
        """
        Initialize display.
        """
        if height != 240 or width not in [320, 240, 135]:
            raise ValueError(
                "Unsupported display. 320x240, 240x240 and 135x240 are supported."
            )

        if dc is None:
            raise ValueError("dc pin is required.")

        self._display_width = self.width = width
        self._display_height = self.height = height
        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self._rotation = rotation % 4
        self._luts = {}
        self._glyphs = {}
        # One buffer reused by every fill, rather than a new one per call: allocating 2KB that
        # often fragments the heap until an allocation fails with memory still free.
        self._fill_buffer = bytearray(_BUFFER_SIZE * 2)
        self._fill_color = None

        self.hard_reset()
        self.soft_reset()
        self.sleep_mode(False)

        self._set_color_mode(COLOR_MODE_65K | COLOR_MODE_16BIT)
        time.sleep_ms(50)
        self.rotation(self._rotation)
        self.inversion_mode(True)
        time.sleep_ms(10)
        self._write(ST7789_NORON)
        time.sleep_ms(10)
        if backlight is not None:
            backlight.value(1)
        self.fill(0)
        self._write(ST7789_DISPON)
        time.sleep_ms(500)

    def _write(self, command=None, data=None):
        """SPI write to the device: commands and data."""
        if self.cs:
            self.cs.off()

        if command is not None:
            self.dc.off()
            self.spi.write(bytes([command]))
        if data is not None:
            self.dc.on()
            self.spi.write(data)
        # Always end the transaction: a command without data (SWRESET, SLPOUT)
        # left CS low, and the display then ignored the init over hardware SPI.
        if self.cs:
            self.cs.on()

    def hard_reset(self):
        """
        Hard reset display.
        """
        if self.cs:
            self.cs.off()
        if self.reset:
            self.reset.on()
        time.sleep_ms(50)
        if self.reset:
            self.reset.off()
        time.sleep_ms(50)
        if self.reset:
            self.reset.on()
        time.sleep_ms(150)
        if self.cs:
            self.cs.on()

    def soft_reset(self):
        """
        Soft reset display.
        """
        self._write(ST7789_SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        if value:
            self._write(ST7789_SLPIN)
        else:
            self._write(ST7789_SLPOUT)

    def inversion_mode(self, value):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
        if value:
            self._write(ST7789_INVON)
        else:
            self._write(ST7789_INVOFF)

    def _set_color_mode(self, mode):
        """
        Set display color mode.

        Args:
            mode (int): color mode
                COLOR_MODE_65K, COLOR_MODE_262K, COLOR_MODE_12BIT,
                COLOR_MODE_16BIT, COLOR_MODE_18BIT, COLOR_MODE_16M
        """
        self._write(ST7789_COLMOD, bytes([mode & 0x77]))

    def rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation (int):
                - 0-Portrait
                - 1-Landscape
                - 2-Inverted Portrait
                - 3-Inverted Landscape
        """

        rotation %= 4
        self._rotation = rotation
        madctl = ROTATIONS[rotation]

        if self._display_width == 320:
            table = WIDTH_320
        elif self._display_width == 240:
            table = WIDTH_240
        elif self._display_width == 135:
            table = WIDTH_135
        else:
            raise ValueError(
                "Unsupported display. 320x240, 240x240 and 135x240 are supported."
            )

        self.width, self.height, self.xstart, self.ystart = table[rotation]
        self._write(ST7789_MADCTL, bytes([madctl]))

    def _set_columns(self, start, end):
        """
        Send CASET (column address set) command to display.

        Args:
            start (int): column start address
            end (int): column end address
        """
        if start <= end <= self.width:
            self._write(ST7789_CASET, _encode_pos(
                start+self.xstart, end + self.xstart))

    def _set_rows(self, start, end):
        """
        Send RASET (row address set) command to display.

        Args:
            start (int): row start address
            end (int): row end address
       """
        if start <= end <= self.height:
            self._write(ST7789_RASET, _encode_pos(
                start+self.ystart, end+self.ystart))

    def _set_window(self, x0, y0, x1, y1):
        """
        Set window to column and row address.

        Args:
            x0 (int): column start address
            y0 (int): row start address
            x1 (int): column end address
            y1 (int): row end address
        """
        self._set_columns(x0, x1)
        self._set_rows(y0, y1)
        self._write(ST7789_RAMWR)

    def vline(self, x, y, length, color):
        """
        Draw vertical line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, 1, length, color)

    def hline(self, x, y, length, color):
        """
        Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, length, 1, color)

    def pixel(self, x, y, color):
        """
        Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        self._set_window(x, y, x, y)
        self._write(None, _encode_pixel(color))

    def blit_buffer(self, buffer, x, y, width, height):
        """
        Copy buffer to display at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._write(None, buffer)

    def rect(self, x, y, w, h, color):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self.hline(x, y, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        self.hline(x, y + h - 1, w, color)

    def fill_rect(self, x, y, width, height, color):
        """
        Draw a rectangle at the given location, size and filled with color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        data = self._fill_buffer
        if color != self._fill_color:
            # Lay the pixel down once and keep doubling it, through a memoryview so that not even
            # the half already filled is copied into a new buffer.
            data[0:2] = _encode_pixel(color)
            view = memoryview(data)
            filled = 2
            while filled < _BUFFER_SIZE * 2:
                data[filled:filled + filled] = view[:filled]
                filled += filled
            self._fill_color = color
        # One transaction for the whole rectangle: letting _write() start a new
        # one per chunk doubled the time a full screen fill takes.
        if self.cs:
            self.cs.off()
        self.dc.on()
        for _ in range(chunks):
            self.spi.write(data)
        if rest:
            self.spi.write(memoryview(data)[:rest * 2])
        if self.cs:
            self.cs.on()

    def fill(self, color):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def line(self, x0, y0, x1, y1, color):
        """
        Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.

        Args:
            x0 (int): Start point x coordinate
            y0 (int): Start point y coordinate
            x1 (int): End point x coordinate
            y1 (int): End point y coordinate
            color (int): 565 encoded color
        """
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        while x0 <= x1:
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def vscrdef(self, tfa, vsa, bfa):
        """
        Set Vertical Scrolling Definition.

        To scroll a 135x240 display these values should be 40, 240, 40.
        There are 40 lines above the display that are not shown followed by
        240 lines that are shown followed by 40 more lines that are not shown.
        You could write to these areas off display and scroll them into view by
        changing the TFA, VSA and BFA values.

        Args:
            tfa (int): Top Fixed Area
            vsa (int): Vertical Scrolling Area
            bfa (int): Bottom Fixed Area
        """
        struct.pack(">HHH", tfa, vsa, bfa)
        self._write(ST7789_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa):
        """
        Set Vertical Scroll Start Address of RAM.

        Defines which line in the Frame Memory will be written as the first
        line after the last line of the Top Fixed Area on the display

        Example:

            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)

        Args:
            vssa (int): Vertical Scrolling Start Address

        """
        self._write(ST7789_VSCSAD, struct.pack(">H", vssa))

    def _glyph(self, font, ch, color, background):
        """
        Render one character to a buffer of 565 pixels, and remember it.

        Characters are expanded one font byte at a time through a 256 entry
        lookup table, which is much quicker than testing every bit, and the
        finished characters are kept: redrawing text in the same colours, a
        counter for instance, then only costs the write to the display.
        """
        key = (id(font), ch, color, background)
        glyph = self._glyphs.get(key)
        if glyph is not None:
            return glyph

        lut = self._luts.get((color, background))
        if lut is None:
            fg = _encode_pixel(color)
            bg = _encode_pixel(background)
            lut = [b"".join(fg if byte & 1 << (7 - bit) else bg
                            for bit in range(8))
                   for byte in range(256)]
            # Building one costs about 50ms, so a few colour pairs are kept.
            if len(self._luts) >= _LUT_CACHE:
                self._luts = {}
            self._luts[(color, background)] = lut

        size = font.WIDTH // 8 * font.HEIGHT
        first = (ch - font.FIRST) * size
        glyph = b"".join(lut[font.FONT[i]] for i in range(first, first + size))
        # ponytail: a 16x32 character costs 1KB, so the cache is emptied rather
        # than grown once it holds _GLYPH_CACHE of them.
        if len(self._glyphs) >= _GLYPH_CACHE:
            self._glyphs = {}
        self._glyphs[key] = glyph
        return glyph

    def text(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        Draw text on display in specified font and colors. Fonts of any width
        that is a multiple of 8 are supported.

        Args:
            font (module): font module to use.
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        for char in text:
            ch = ord(char)
            if (font.FIRST <= ch < font.LAST
                    and x0 + font.WIDTH <= self.width
                    and y0 + font.HEIGHT <= self.height):
                self._set_window(x0, y0, x0 + font.WIDTH - 1,
                                 y0 + font.HEIGHT - 1)
                self._write(None, self._glyph(font, ch, color, background))
            x0 += font.WIDTH

    def bitmap(self, bitmap, x, y, index=0):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module

        """
        bitmap_size = bitmap.HEIGHT * bitmap.WIDTH
        buffer_len = bitmap_size * 2
        buffer = bytearray(buffer_len)
        bs_bit = bitmap.BPP * bitmap_size * index if index > 0 else 0

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bitmap.BPP):
                color_index <<= 1
                color_index |= (bitmap.BITMAP[bs_bit // 8]
                                & 1 << (7 - (bs_bit % 8))) > 0
                bs_bit += 1

            color = bitmap.PALETTE[color_index]
            buffer[i] = color & 0xff00 >> 8
            buffer[i + 1] = color_index & 0xff

        to_col = x + bitmap.WIDTH - 1
        to_row = y + bitmap.HEIGHT - 1
        if self.width > to_col and self.height > to_row:
            self._set_window(x, y, to_col, to_row)
            self._write(None, buffer)

    # @micropython.native
    def write(self, font, string, x, y, fg=WHITE, bg=BLACK):
        """
        Write a string using a converted true-type font on the display starting
        at the specified column and row

        Args:
            font (font): The module containing the converted true-type font
            s (string): The string to write
            x (int): column to start writing
            y (int): row to start writing
            fg (int): foreground color, optional, defaults to WHITE
            bg (int): background color, optional, defaults to BLACK
        """
        buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
        buffer = bytearray(buffer_len)
        fg_hi = (fg & 0xff00) >> 8
        fg_lo = fg & 0xff

        bg_hi = (bg & 0xff00) >> 8
        bg_lo = bg & 0xff

        for character in string:
            try:
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                if font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]

                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]

                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT * 2

                for i in range(0, buffer_needed, 2):
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        buffer[i] = fg_hi
                        buffer[i + 1] = fg_lo
                    else:
                        buffer[i] = bg_hi
                        buffer[i + 1] = bg_lo

                    bs_bit += 1

                to_col = x + char_width - 1
                to_row = y + font.HEIGHT - 1
                if self.width > to_col and self.height > to_row:
                    self._set_window(x, y, to_col, to_row)
                    self._write(None, buffer[:buffer_needed])

                x += char_width

            except ValueError:
                pass

    def write_width(self, font, string):
        """
        Returns the width in pixels of the string if it was written with the
        specified font

        Args:
            font (font): The module containing the converted true-type font
            string (string): The string to measure
        """
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]

            except ValueError:
                pass

        return width
