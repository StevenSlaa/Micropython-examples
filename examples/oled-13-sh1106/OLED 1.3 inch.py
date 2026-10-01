# A 1.3 inch 128x64 SH1106 OLED on a Raspberry Pi Pico.
#
# Cycles through a few scenes: a geometry check, bouncing balls, a scrolling sine wave and a
# live dashboard with the Pico's own temperature sensor. 128x64 is the panel the SH1106 was
# made for, so the driver's defaults are right and no setup is needed.

from machine import Pin, SoftI2C, ADC
from time import sleep_ms, ticks_ms, ticks_diff
from math import sin, pi
import framebuf
from sh1106 import SH1106_I2C

# Configuration
sda_pin = 6
scl_pin = 7
address = 0x3C
scene_ms = 6000  # how long each scene runs

width = 128
height = 64

# SoftI2C rather than I2C(1): on this wiring the hardware peripheral answers a scan but
# fails every write with EIO, which usually means weak pull-ups. SoftI2C tolerates them.
i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
display = SH1106_I2C(width, height, i2c, addr=address)


def big_text(text, x, y, scale=2):
    # The built-in font is 8x8 only, so draw it into a scratch buffer and blow each pixel up.
    w = len(text) * 8
    buf = framebuf.FrameBuffer(bytearray(w), w, 8, framebuf.MONO_HLSB)
    buf.text(text, 0, 0, 1)
    for py in range(8):
        for px in range(w):
            if buf.pixel(px, py):
                display.fill_rect(x + px * scale, y + py * scale, scale, scale, 1)


def centered(text, y):
    display.text(text, (width - len(text) * 8) // 2, y, 1)


def splash():
    # The border should sit exactly on the edges of the glass. A gap or a clipped edge on the
    # left or right means the column offset is wrong (or the chip is really an SSD1306).
    display.fill(0)
    display.rect(0, 0, width, height, 1)
    big_text("SH1106", 16, 10)
    centered("1.3in  128x64", 34)
    centered("Pico + MicroPython", 48)
    display.show()
    sleep_ms(scene_ms // 2)


def balls():
    things = [[20, 10, 2, 1, 4], [60, 30, -1, 2, 6], [100, 50, 3, -1, 3]]  # x, y, dx, dy, r
    end = ticks_ms() + scene_ms
    while ticks_diff(end, ticks_ms()) > 0:
        display.fill(0)
        display.rect(0, 0, width, height, 1)
        for b in things:
            x, y, dx, dy, r = b
            if not r < x + dx < width - r - 1:
                b[2] = dx = -dx
            if not r < y + dy < height - r - 1:
                b[3] = dy = -dy
            b[0] = x = x + dx
            b[1] = y = y + dy
            # The driver's ellipse() drops framebuf's fill argument, so fill it a row at a time.
            for oy in range(-r, r + 1):
                ox = int((r * r - oy * oy) ** 0.5)
                display.hline(x - ox, y + oy, 2 * ox + 1, 1)
        display.show()


def wave():
    phase = 0.0
    end = ticks_ms() + scene_ms
    while ticks_diff(end, ticks_ms()) > 0:
        display.fill(0)
        display.text("sin(x)", 0, 0, 1)
        display.hline(0, 36, width, 1)
        prev = None
        for x in range(width):
            y = 36 - int(20 * sin(x * 2 * pi / 64 + phase))
            if prev is not None:
                display.line(x - 1, prev, x, y, 1)
            prev = y
        display.show()
        phase += 0.25


def dashboard():
    # ADC 4 is the RP2040's internal sensor: 0.706V at 27C, falling 1.721mV per degree.
    # ponytail: uncalibrated, it reads a few degrees off; adjust temp_trim against a thermometer.
    sensor = ADC(4)
    temp_trim = 0.0
    history = []
    end = ticks_ms() + scene_ms * 2
    while ticks_diff(end, ticks_ms()) > 0:
        volts = sensor.read_u16() * 3.3 / 65535
        temp = 27 - (volts - 0.706) / 0.001721 + temp_trim
        history = (history + [temp])[-width:]

        display.fill(0)
        display.text("Pico temp", 0, 0, 1)
        big_text("%.1fC" % temp, 0, 12)
        up = ticks_ms() // 1000
        display.text("up %02d:%02d" % (up // 60 % 60, up % 60), 72, 0, 1)

        # Graph of the history in the bottom 32 rows, scaled to its own range.
        lo, hi = min(history), max(history)
        span = max(hi - lo, 1)
        for i, t in enumerate(history):
            h = 1 + int((t - lo) / span * 28)
            display.vline(i, height - h, h, 1)
        display.show()
        sleep_ms(100)


while True:
    for scene in (splash, balls, wave, dashboard):
        scene()
