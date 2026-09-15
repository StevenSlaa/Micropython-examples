"""AXS15231B QSPI display and touch driver for MicroPython on the ESP32-S3.

Written for the 3.4 inch 180x640 panel of the LilyGO T-Display-S3 Long, whose AXS15231B controller
also handles the capacitive touch. MicroPython has no QSPI bus, so the display is driven with
Viper-compiled writes to the ESP32-S3's GPIO register, like st7789_parallel.py. The drawing methods
come from rgb565_display.py.
"""

import micropython
from array import array
from machine import Pin
from micropython import const
from os import uname
from time import sleep_ms
from rgb565_display import RGB565Display, color565, BLACK, NAVY, BLUE, GREEN, CYAN, RED, MAGENTA, YELLOW, WHITE

SLPIN = const(0x10)
SLPOUT = const(0x11)
INVOFF = const(0x20)
INVON = const(0x21)
DISPOFF = const(0x28)
DISPON = const(0x29)
CASET = const(0x2A)
RASET = const(0x2B)

# ponytail: the T-Display-S3 Long's QSPI pins are fixed in the Viper code: CS 12, D0 13, D3 14,
# SCK 17, D1 18, D2 21, all in GPIO_OUT_REG. Another board needs new masks here.
_BUS_MASK = const(0x266000)  # D0, D1, D2, D3 and SCK
_IDLE_HIGH = const(0x204000)  # D2 and D3 stay high outside the quad data phase, as ESP-IDF keeps them
_SCK = const(0x20000)
# GPIO_OUT_REG bits that put each 4 bit value on D0..D3, looked up instead of computed per nibble
_NIBBLE_BITS = array("I", ((n & 1) << 13 | (n >> 1 & 1) << 18 | (n >> 2 & 1) << 21 | (n >> 3 & 1) << 14 for n in range(16)))

_WIDTH = const(180)  # the panel's own size, in portrait
_HEIGHT = const(640)
_READ_TOUCH = b"\xb5\xab\xa5\x5a\x00\x00\x00\x08"


# Every transfer starts with a 32 bit header on one line: 02 00 <command> 00 for a command, and
# 32 00 2C 00 for pixels, whose data then follows on all four lines, a nibble per clock.
@micropython.viper
def _single(value: int, bits: int):
    """Clock the low `bits` bits of value out on D0, most significant first (SPI mode 0)."""
    out = ptr32(0x60004004)  # GPIO_OUT_REG
    level = int(out[0])
    idle = (level ^ (level & _BUS_MASK)) | _IDLE_HIGH
    while bits > 0:
        bits -= 1
        level = idle | ((value >> bits) & 1) << 13
        out[0] = level
        out[0] = level | _SCK
    out[0] = idle


@micropython.viper
def _quad(data, order):
    """Send an RGB565 buffer on D0..D3, high nibble first, as the data phase of a QIO transfer.

    The panel fills its window row by row. `order` says how to walk the buffer so that a rotated
    picture still arrives that way: [rows, columns, first pixel, step per row, step per column].
    """
    out = ptr32(0x60004004)
    level = int(out[0])
    base = level ^ (level & _BUS_MASK)
    source = ptr8(data)
    walk = ptr32(order)
    rows = int(walk[0])
    columns = int(walk[1])
    row_start = int(walk[2])
    row_step = int(walk[3])
    column_step = int(walk[4])
    bits = ptr32(_NIBBLE_BITS)
    for _ in range(rows):
        pixel = row_start
        for _ in range(columns):
            index = pixel << 1
            high = int(source[index])
            low = int(source[index + 1])
            level = base | int(bits[high >> 4])
            out[0] = level
            out[0] = level | _SCK
            level = base | int(bits[high & 15])
            out[0] = level
            out[0] = level | _SCK
            level = base | int(bits[low >> 4])
            out[0] = level
            out[0] = level | _SCK
            level = base | int(bits[low & 15])
            out[0] = level
            out[0] = level | _SCK
            pixel += column_step
        row_start += row_step
    out[0] = base | _IDLE_HIGH


@micropython.viper
def _quad_fill(color: int, count: int):
    """Send one RGB565 colour count times on D0..D3 without a pixel buffer."""
    out = ptr32(0x60004004)
    level = int(out[0])
    base = level ^ (level & _BUS_MASK)
    n = color >> 12 & 15
    first = base | (n & 1) << 13 | (n >> 1 & 1) << 18 | (n >> 2 & 1) << 21 | (n >> 3 & 1) << 14
    n = color >> 8 & 15
    second = base | (n & 1) << 13 | (n >> 1 & 1) << 18 | (n >> 2 & 1) << 21 | (n >> 3 & 1) << 14
    n = color >> 4 & 15
    third = base | (n & 1) << 13 | (n >> 1 & 1) << 18 | (n >> 2 & 1) << 21 | (n >> 3 & 1) << 14
    n = color & 15
    fourth = base | (n & 1) << 13 | (n >> 1 & 1) << 18 | (n >> 2 & 1) << 21 | (n >> 3 & 1) << 14
    for _ in range(count):
        out[0] = first
        out[0] = first | _SCK
        out[0] = second
        out[0] = second | _SCK
        out[0] = third
        out[0] = third | _SCK
        out[0] = fourth
        out[0] = fourth | _SCK
    out[0] = base | _IDLE_HIGH


def _to_panel(rotation, x, y):
    """Map a point on the rotated screen to the panel's own portrait coordinates."""
    if rotation == 0:
        return x, y
    if rotation == 1:  # landscape, USB on the right
        return _WIDTH - 1 - y, x
    if rotation == 2:
        return _WIDTH - 1 - x, _HEIGHT - 1 - y
    return y, _HEIGHT - 1 - x  # landscape, USB on the left


class AXS15231B(RGB565Display):
    """The 180x640 AXS15231B display of the LilyGO T-Display-S3 Long.

    The pins are fixed by the board, so there are none to pass. Rotation 0 is portrait with the
    USB port at the bottom, 1 is 640x180 landscape with USB on the right, 2 is portrait upside down
    and 3 is landscape with USB on the left. The panel itself cannot rotate, so the driver does it.
    """

    def __init__(self, rotation=0, backlight=True):
        if "ESP32-S3" not in uname().machine:
            raise ValueError("this driver writes ESP32-S3 GPIO registers")
        self._cs = Pin(12, Pin.OUT, value=1)
        for pin in (13, 18, 17):  # D0, D1, SCK
            Pin(pin, Pin.OUT, value=0)
        for pin in (21, 14):  # D2, D3
            Pin(pin, Pin.OUT, value=1)
        self._reset = Pin(16, Pin.OUT, value=1)  # also resets the touch controller
        self._backlight = Pin(1, Pin.OUT, value=0)
        self._order = array("i", (0, 0, 0, 0, 0))
        self._one_pixel = array("i", (1, 1, 0, 0, 0))
        self._window = (0, 0, 0, 0)
        self.rotation(rotation)

        self.reset()
        # LilyGO's factory firmware sends only these; the rest of the setup is stored in the panel.
        self._command(SLPOUT)
        sleep_ms(200)
        self._command(DISPON)
        self.backlight(backlight)

    def rotation(self, rotation):
        """Set rotation 0, 1, 2 or 3 and update width and height. Drawn pixels stay as they are."""
        if rotation not in (0, 1, 2, 3):
            raise ValueError("rotation must be 0, 1, 2 or 3")
        self._rotation = rotation
        self.width, self.height = (_HEIGHT, _WIDTH) if rotation & 1 else (_WIDTH, _HEIGHT)

    def _command(self, command, value=0, bits=0):
        self._cs(0)
        _single(0x02000000 | command << 8, 32)
        if bits:
            _single(value, bits)
        self._cs(1)

    def reset(self):
        """Hardware-reset the display and touch controller."""
        self._reset(0)
        sleep_ms(130)
        self._reset(1)
        sleep_ms(300)

    def backlight(self, enabled=True):
        self._backlight(1 if enabled else 0)

    def invert(self, enabled=True):
        self._command(INVON if enabled else INVOFF)

    def sleep(self, enabled=True):
        """Enter or leave the controller's sleep mode."""
        self._command(SLPIN if enabled else SLPOUT)
        sleep_ms(200)

    def display(self, enabled=True):
        """Turn the image on or off without changing the backlight."""
        self._command(DISPON if enabled else DISPOFF)

    def _set_window(self, x0, y0, x1, y1):
        ax, ay = _to_panel(self._rotation, x0, y0)
        bx, by = _to_panel(self._rotation, x1, y1)
        self._window = (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))

    def _first_column_alone(self):
        # Measured on the panel: it garbles a window one column wide but several rows tall, and a
        # wider window whose first column is 3, 7, 11 and so on. Such a window's first column goes
        # out a pixel at a time, and the rest as a normal window from the next column.
        left, top, right, bottom = self._window
        if left == right:
            return top != bottom
        return left % 4 == 3

    def _send_window(self, left, top, right, bottom):
        self._command(CASET, left << 16 | right, 32)
        self._command(RASET, top << 16 | bottom, 32)

    def _send_buffer(self, buffer, order):
        self._cs(0)
        _single(0x32002C00, 32)
        _quad(buffer, order)
        self._cs(1)

    def _send_fill(self, color, count):
        self._cs(0)
        _single(0x32002C00, 32)
        _quad_fill(color, count)
        self._cs(1)

    def _write_pixels(self, buffer, width, height):
        # How to walk a width x height buffer so the panel receives its rows in its own order:
        # [rows, columns, first pixel, step per row, step per column].
        order = self._order
        rotation = self._rotation
        if rotation == 0:
            order[0], order[1], order[2], order[3], order[4] = height, width, 0, width, 1
        elif rotation == 1:
            order[0], order[1], order[2], order[3], order[4] = width, height, (height - 1) * width, 1, -width
        elif rotation == 2:
            order[0], order[1], order[2], order[3], order[4] = height, width, width * height - 1, -width, -1
        else:
            order[0], order[1], order[2], order[3], order[4] = width, height, width - 1, -1, width
        left, top, right, bottom = self._window
        # Peeling off a column on 3, 7, 11... can leave a single column, which also needs it: loop.
        while self._first_column_alone():
            pixel = self._one_pixel
            for row in range(order[0]):
                self._send_window(left, top + row, left, top + row)
                pixel[2] = order[2] + row * order[3]
                self._send_buffer(buffer, pixel)
            left += 1
            if left > right:
                return
            self._window = (left, top, right, bottom)
            order[1] -= 1
            order[2] += order[4]
        self._send_window(left, top, right, bottom)
        self._send_buffer(buffer, order)

    def _fill_pixels(self, color, count):
        left, top, right, bottom = self._window
        while self._first_column_alone():
            for row in range(top, bottom + 1):
                self._send_window(left, row, left, row)
                self._send_fill(color, 1)
            left += 1
            if left > right:
                return
            self._window = (left, top, right, bottom)
        self._send_window(left, top, right, bottom)
        self._send_fill(color, (right - left + 1) * (bottom - top + 1))

class AXS15231BTouch:
    """The capacitive touch built into the T-Display-S3 Long's AXS15231B, on I2C address 0x3B.

    Give it the same ``rotation`` as the display, so touches arrive in the coordinates you draw with,
    and call read() every frame: the controller hands out each report only once.

    ``calibration`` holds the raw readings at the left, right, top and bottom edges of the portrait
    screen, measured on a T-Display-S3 Long. The centre of a fingertip stays a few millimetres from
    the edge, so a line traced along the edge lands slightly inside it: that is the finger.
    """

    def __init__(self, i2c, rotation=0, calibration=(6, 176, 627, 10), address=0x3B):
        self._i2c = i2c
        self._address = address
        self._buffer = bytearray(8)
        self.rotation = rotation
        self.calibration = calibration
        self._point = None
        self._counter = -1

    def read(self):
        """Return the touched point as (x, y) in display coordinates, or None when nothing touches."""
        buffer = self._buffer
        try:
            self._i2c.writeto(self._address, _READ_TOUCH)
            self._i2c.readfrom_into(self._address, buffer)
        except OSError:
            return self._point
        if not any(buffer):  # idle
            self._point = None
            return None
        # A report has gesture 0 in byte 0, one or two points in byte 1, and a counter and the counter
        # plus one in bytes 6 and 7. Between reports the controller answers with garbled frames or
        # repeats the last one, including while a finger rests without moving: those change nothing.
        if buffer[0] or not 0 < buffer[1] & 0x0F <= 2 or (buffer[6] + 1) & 0xFF != buffer[7]:
            return self._point
        along = (buffer[2] & 0x0F) << 8 | buffer[3]  # along the 640 pixel side, from the USB end
        across = (buffer[4] & 0x0F) << 8 | buffer[5]
        if along >= _HEIGHT or across >= _WIDTH or buffer[6] == self._counter:
            return self._point
        self._counter = buffer[6]
        if buffer[2] >> 6 == 1:  # the finger lifted
            self._point = None
            return None
        left, right, top, bottom = self.calibration
        x = min(max((across - left) * (_WIDTH - 1) // (right - left), 0), _WIDTH - 1)
        y = min(max((top - along) * (_HEIGHT - 1) // (top - bottom), 0), _HEIGHT - 1)
        rotation = self.rotation
        if rotation == 1:
            x, y = y, _WIDTH - 1 - x
        elif rotation == 2:
            x, y = _WIDTH - 1 - x, _HEIGHT - 1 - y
        elif rotation == 3:
            x, y = _HEIGHT - 1 - y, x
        self._point = (x, y)
        return self._point
