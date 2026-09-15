"""ST7789 8-bit (Intel 8080) parallel display driver for MicroPython.

The defaults describe the 170x320 panel in the LilyGO/TTGO T-Display-S3. Drawing methods come
from rgb565_display.py; this module only knows how to talk to the ST7789 over its parallel bus.
"""

import micropython
from micropython import const
from os import uname
from time import sleep_ms
from rgb565_display import RGB565Display, color565, BLACK, NAVY, BLUE, GREEN, CYAN, RED, MAGENTA, YELLOW, WHITE


NOP = const(0x00)
SWRESET = const(0x01)
SLPIN = const(0x10)
SLPOUT = const(0x11)
NORON = const(0x13)
INVOFF = const(0x20)
INVON = const(0x21)
DISPOFF = const(0x28)
DISPON = const(0x29)
CASET = const(0x2A)
RASET = const(0x2B)
RAMWR = const(0x2C)
MADCTL = const(0x36)
COLMOD = const(0x3A)

# This panel reports RGB ordering in its configuration, but the physical glass on the tested
# T-Display-S3 needs MADCTL's BGR bit. Without it red and blue are exchanged.
_MADCTL_BGR = const(0x08)
_MADCTL_ROTATION = (0x00, 0x60, 0xC0, 0xA0)
_CHUNK_PIXELS = const(512)
_NO_COMMAND = const(-1)


# The Viper decorator must be spelled exactly @micropython.viper: the compiler recognises that
# name, and micropython.viper does not exist as a runtime attribute.
# ponytail: firmware without the native emitter cannot import this module; every ESP32-S3 build has it.
@micropython.viper
def _bus_viper(command: int, data, length: int):
    """Send an optional command byte, then length data bytes (T-Display-S3 pins only)."""
    out_set = ptr32(0x60004008)  # GPIO0..31 W1TS: DC is GPIO7, WR is GPIO8
    out_clear = ptr32(0x6000400C)
    out1 = ptr32(0x60004010)  # GPIO32..53: D0..D3 are bits 7..10, D4..D7 bits 13..16
    # ponytail: OUT1 is read once, so an IRQ changing GPIO32..48 mid-write is overwritten.
    other = int(out1[0]) & 0x3FE187F

    if command >= 0:
        out_clear[0] = 0x80
        out1[0] = other | ((command & 0x0F) << 7) | ((command & 0xF0) << 9)
        out_clear[0] = 0x100
        out_set[0] = 0x100  # WR rising edge: the ST7789 latches the byte
        out_set[0] = 0x80

    source = ptr8(data)
    for index in range(length):
        value = int(source[index])
        out1[0] = other | ((value & 0x0F) << 7) | ((value & 0xF0) << 9)
        out_clear[0] = 0x100
        out_set[0] = 0x100


@micropython.viper
def _fill_viper(color: int, count: int):
    """Repeat an RGB565 pixel count times without a pixel buffer (T-Display-S3 pins only)."""
    out_set = ptr32(0x60004008)
    out_clear = ptr32(0x6000400C)
    out1 = ptr32(0x60004010)
    other = int(out1[0]) & 0x3FE187F
    high = (color >> 8) & 0xFF
    low = color & 0xFF
    high_bits = other | ((high & 0x0F) << 7) | ((high & 0xF0) << 9)
    low_bits = other | ((low & 0x0F) << 7) | ((low & 0xF0) << 9)

    if high == low:
        # Black, white and other symmetric colours: set the bus once and only pulse WR.
        out1[0] = high_bits
        for _ in range(count * 2):
            out_clear[0] = 0x100
            out_set[0] = 0x100
        return

    for _ in range(count):
        out1[0] = high_bits
        out_clear[0] = 0x100
        out_set[0] = 0x100
        out1[0] = low_bits
        out_clear[0] = 0x100
        out_set[0] = 0x100


class ST7789Parallel(RGB565Display):
    """An ST7789 connected through its 8-bit Intel 8080 write interface.

    ``data_pins`` must contain Pin objects in D0 through D7 order. ``wr``,
    ``dc`` and ``cs`` are required Pin objects. ``reset``, ``rd`` and
    ``backlight`` are optional Pins. The default dimensions and offsets are
    for the T-Display-S3's 170x320 panel.

    Rotation 0 is 170x320 portrait; rotation 1 is 320x170 landscape. The
    other two values turn those orientations upside down. ``fast=True`` uses
    direct ESP32-S3 registers and is only valid with the T-Display-S3 pin map.
    """

    def __init__(
        self,
        data_pins,
        wr,
        dc,
        cs,
        reset=None,
        rd=None,
        backlight=None,
        width=170,
        height=320,
        x_offset=35,
        y_offset=0,
        rotation=1,
        inversion=True,
        fast=False,
    ):
        if len(data_pins) != 8:
            raise ValueError("data_pins must contain D0 through D7")
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if rotation not in (0, 1, 2, 3):
            raise ValueError("rotation must be 0, 1, 2 or 3")
        if fast and "ESP32-S3" not in uname().machine:
            raise ValueError("fast mode writes ESP32-S3 GPIO registers")

        self._data_pins = tuple(data_pins)
        self._wr = wr
        self._dc = dc
        self._reset = reset
        self._backlight = backlight
        self._native_width = width
        self._native_height = height
        self._offsets = (
            (x_offset, y_offset),
            (y_offset, x_offset),
            (x_offset, y_offset),
            (y_offset, x_offset),
        )
        self._last_byte = None
        self._window = bytearray(4)
        self.fast = fast
        self._bus = _bus_viper if fast else self._bus_pins
        self._rotation = rotation
        self.width = width
        self.height = height
        self.x_offset = x_offset
        self.y_offset = y_offset

        for pin in self._data_pins:
            pin.init(pin.OUT, value=0)
        wr.init(wr.OUT, value=1)
        dc.init(dc.OUT, value=1)
        # ponytail: CS stays selected; toggle it per write only if another device shares this bus.
        cs.init(cs.OUT, value=0)
        if rd is not None:
            rd.init(rd.OUT, value=1)  # This driver only writes.
        if reset is not None:
            reset.init(reset.OUT, value=1)
        if backlight is not None:
            backlight.init(backlight.OUT, value=0)

        self.reset()
        self._initialize(inversion)
        self.rotation(rotation)
        self.backlight(True)

    def _write_byte(self, value):
        value &= 0xFF
        changed = 0xFF if self._last_byte is None else value ^ self._last_byte
        if changed:
            for bit, pin in enumerate(self._data_pins):
                if changed & (1 << bit):
                    pin.value((value >> bit) & 1)
            self._last_byte = value
        self._wr.value(0)
        self._wr.value(1)

    def _bus_pins(self, command, data, length):
        """Portable pin-by-pin equivalent of _bus_viper for any pin map."""
        if command >= 0:
            self._dc.value(0)
            self._write_byte(command)
            self._dc.value(1)
        write = self._write_byte
        for index in range(length):
            write(data[index])

    def _command(self, command, data=b""):
        self._bus(command, data, len(data))

    def reset(self):
        """Hardware-reset the controller when a reset Pin was supplied."""
        if self._reset is None:
            return
        self._reset.value(1)
        sleep_ms(5)
        self._reset.value(0)
        sleep_ms(20)
        self._reset.value(1)
        sleep_ms(150)

    def _initialize(self, inversion):
        # INIT_SEQUENCE_3 from TFT_eSPI, selected by LilyGO for this panel.
        self._command(SLPOUT)
        sleep_ms(120)
        self._command(NORON)
        self._command(MADCTL, bytes((_MADCTL_BGR,)))
        self._command(0xB6, b"\x0a\x82")
        self._command(0xB0, b"\x00\xe0")
        self._command(COLMOD, b"\x55")  # 16-bit RGB565
        sleep_ms(10)
        self._command(0xB2, b"\x0c\x0c\x00\x33\x33")
        self._command(0xB7, b"\x35")
        self._command(0xBB, b"\x28")
        self._command(0xC0, b"\x0c")
        self._command(0xC2, b"\x01\xff")
        self._command(0xC3, b"\x10")
        self._command(0xC4, b"\x20")
        self._command(0xC6, b"\x0f")
        self._command(0xD0, b"\xa4\xa1")
        self._command(
            0xE0,
            b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17",
        )
        self._command(
            0xE1,
            b"\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e",
        )
        self.invert(inversion)
        sleep_ms(120)
        self._command(DISPON)
        sleep_ms(120)

    def rotation(self, rotation):
        """Set rotation to 0, 1, 2 or 3 and update width and height."""
        if rotation not in (0, 1, 2, 3):
            raise ValueError("rotation must be 0, 1, 2 or 3")
        self._rotation = rotation
        if rotation & 1:
            self.width, self.height = self._native_height, self._native_width
        else:
            self.width, self.height = self._native_width, self._native_height
        self.x_offset, self.y_offset = self._offsets[rotation]
        self._command(MADCTL, bytes((_MADCTL_ROTATION[rotation] | _MADCTL_BGR,)))

    def invert(self, enabled=True):
        """Enable the colour inversion required by the T-Display-S3 panel."""
        self._command(INVON if enabled else INVOFF)

    def sleep(self, enabled=True):
        """Enter or leave the controller's sleep mode."""
        self._command(SLPIN if enabled else SLPOUT)
        sleep_ms(120)

    def backlight(self, enabled=True):
        """Turn the backlight fully on or off, if its Pin was supplied."""
        if self._backlight is not None:
            self._backlight.value(1 if enabled else 0)

    def display(self, enabled=True):
        """Turn display scanning on or off without changing the backlight."""
        self._command(DISPON if enabled else DISPOFF)

    def _set_window(self, x0, y0, x1, y1):
        """Select a RAM window and start RAMWR; the bus is left in data mode."""
        bus = self._bus
        window = self._window
        x0 += self.x_offset
        x1 += self.x_offset
        window[0] = x0 >> 8
        window[1] = x0 & 0xFF
        window[2] = x1 >> 8
        window[3] = x1 & 0xFF
        bus(CASET, window, 4)
        y0 += self.y_offset
        y1 += self.y_offset
        window[0] = y0 >> 8
        window[1] = y0 & 0xFF
        window[2] = y1 >> 8
        window[3] = y1 & 0xFF
        bus(RASET, window, 4)
        bus(RAMWR, window, 0)

    def _write_pixels(self, buffer, width, height):
        self._bus(_NO_COMMAND, buffer, len(buffer))

    def _fill_pixels(self, color, count):
        if self.fast:
            _fill_viper(color, count)
            return
        pixel = bytes((color >> 8, color & 0xFF))
        chunk = pixel * _CHUNK_PIXELS
        while count >= _CHUNK_PIXELS:
            self._bus(_NO_COMMAND, chunk, len(chunk))
            count -= _CHUNK_PIXELS
        self._bus(_NO_COMMAND, pixel * count, count * 2)
