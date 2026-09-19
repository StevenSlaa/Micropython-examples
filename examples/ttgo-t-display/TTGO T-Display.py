# Written by Steven Slaa

import framebuf
import machine
from machine import Pin, SPI
from math import sin
from time import sleep_ms, ticks_diff, ticks_ms
import st7789py as st7789
from st7789py import color565
import pulsar_ui

# Configuration
# The display and both buttons are built into the board, so there is nothing to wire or choose.
lcd_sck, lcd_mosi, lcd_cs, lcd_dc, lcd_res, lcd_bl = 18, 19, 5, 16, 23, 4
button_left, button_right = 0, 35
# 1 or 3 is landscape (240x135), which the layout needs. Upside down? Use the other one.
rotation = 1
# MOSI is not one of the ESP32's direct SPI pins on this board, so the bus runs through the GPIO
# matrix and stops here. Asking for more crashes the board rather than slowing it down.
baudrate = 26666666
# how long one frame lasts: 50 ms is 20 frames a second
frame_ms = 50

# The board starts at 160MHz. Drawing is what this costs the most, so run it flat out.
machine.freq(240000000)

spi = SPI(1, baudrate=baudrate, sck=Pin(lcd_sck), mosi=Pin(lcd_mosi))
display = st7789.ST7789(
    spi, 135, 240,
    reset=Pin(lcd_res, Pin.OUT), dc=Pin(lcd_dc, Pin.OUT), cs=Pin(lcd_cs, Pin.OUT),
    backlight=Pin(lcd_bl, Pin.OUT), rotation=rotation,
)
# Both buttons pull their pin low when pressed; GPIO 35 has an external pull-up on the board.
buttons = (Pin(button_left, Pin.IN, Pin.PULL_UP), Pin(button_right, Pin.IN))

# Colours, the same palette as the other Pulsar IoT dashboards
BACKGROUND = color565(12, 16, 28)
PANEL = color565(30, 36, 56)
MUTED = color565(140, 150, 175)
BRAND = color565(240, 64, 64)  # the red of "IoT" in the logo
AREA = color565(70, 26, 34)  # the same red, dimmed, under the chart line
GOOD = color565(60, 200, 110)

# Layout of the 240x135 screen
HEADER = 28
BODY = HEADER + 4
BAR_X, BAR_WIDTH = 6, 228
CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT = 6, 54, 228, 76
CHART_LOW, CHART_HIGH = 15, 30  # the chart's scale in °C, fixed because it scrolls
SCROLL = 3  # pixels the chart moves left every frame

# The chart lives in memory: each frame it slides left with framebuf's fast scroll(), only the new
# columns on the right are drawn, and it reaches the screen in one blit, so it never shows half a
# frame. framebuf keeps a colour's two bytes the other way round, hence the INK_ swap.
chart_pixels = bytearray(CHART_WIDTH * CHART_HEIGHT * 2)
chart = framebuf.FrameBuffer(chart_pixels, CHART_WIDTH, CHART_HEIGHT, framebuf.RGB565)
INK_BACKGROUND, INK_GRID, INK_AREA, INK_LINE = (
    ((c & 0xFF) << 8) | (c >> 8) for c in (BACKGROUND, PANEL, AREA, BRAND))

def swapped(colour):
    """framebuf keeps a colour's two bytes the other way round from the display."""
    return ((colour & 0xFF) << 8) | (colour >> 8)


_luts = {}
# One buffer every label is built in, claimed at startup while the heap is still whole: a label
# is up to 7KB and asking for that much in one piece later fails long before memory runs out.
_label_buffer = bytearray(240 * 16 * 2)


def lut_for(colour, background, scale):
    """
    A table turning one byte of a 1 bit bitmap into 8 pixels, each `scale` wide.

    Expanding a byte at a time rather than a pixel at a time is about ten times quicker, and the
    logo alone is 2400 pixels. A table costs 4KB, so only a few colour pairs are worth keeping.
    """
    lut = _luts.get((colour, background, scale))
    if lut is None:
        ink = bytes((colour >> 8, colour & 0xFF)) * scale
        paper = bytes((background >> 8, background & 0xFF)) * scale
        lut = [b"".join(ink if byte & 128 >> bit else paper for bit in range(8))
               for byte in range(256)]
        _luts[(colour, background, scale)] = lut
    return lut


def label(text, x, y, colour=MUTED, background=BACKGROUND, scale=2):
    """
    Draws text in framebuf's built in 8x8 font, `scale` times its size.

    The driver's own font is 16x32, which on a screen this size turns every heading into a
    shouted word. Headings are drawn at 16x16 instead: framebuf writes the characters into a one
    bit buffer, each row of that is widened through the table, and each row is repeated `scale`
    times.
    """
    width = len(text) * 8
    row_bytes = width // 8
    characters = bytearray(width)
    framebuf.FrameBuffer(characters, width, 8, framebuf.MONO_HLSB).text(text, 0, 0, 1)
    lut = lut_for(colour, background, scale)
    filled = 0
    for row in range(8):
        pixels = b"".join(lut[characters[row * row_bytes + byte]] for byte in range(row_bytes))
        for _ in range(scale):
            _label_buffer[filled:filled + len(pixels)] = pixels
            filled += len(pixels)
    display.blit_buffer(memoryview(_label_buffer)[:filled], x, y, width * scale, 8 * scale)


def mono(bitmap, x, y, width, height, colour, background):
    """Draws a 1 bit MONO_HLSB bitmap in two colours, a byte at a time through the same table."""
    lut = lut_for(colour, background, 1)
    # A bitmap's rows are whole bytes, so the drawn width is rounded up to the next multiple of 8.
    display.blit_buffer(b"".join(lut[byte] for byte in bitmap), x, y, (width + 7) // 8 * 8, height)


def big(text, x, y, colour=st7789.WHITE, background=BACKGROUND):
    """Draws `text` in the large Poppins characters from pulsar_ui.py, and returns where it ends."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        mono(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, colour, background)
        x += width
    return x


def value(text, x, y, colour=st7789.WHITE, until=234):
    """Draws a number and wipes whatever a longer number left behind, so nothing has to blink."""
    end = big(text, x, y, colour)
    display.fill_rect(end, y, until - end, pulsar_ui.FONT_HEIGHT, BACKGROUND)


def half(left, right):
    """Two numbers side by side, each wiping only its own half of the screen."""
    text, x, colour = left
    value(text, x, 70, colour, 120)
    text, x, colour = right
    value(text, x, 70, colour)


def bar(y, percent, colour):
    """A bar the width of the screen: the filled part, then the track behind it."""
    filled = int(BAR_WIDTH * max(0, min(percent, 100)) // 100)
    display.fill_rect(BAR_X, y, filled, 6, colour)
    display.fill_rect(BAR_X + filled, y, BAR_WIDTH - filled, 6, PANEL)


def header():
    """The logo and the line under it, drawn once: only the dots beside it ever change."""
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        mono(bitmap, x, y, width, height, BRAND if colour == "RED" else st7789.WHITE, BACKGROUND)
    display.hline(0, HEADER, 240, PANEL)


def dots(page):
    """A dot for each page, with the current one lit."""
    for index in range(len(PAGES)):
        display.fill_rect(200 + index * 13, 11, 7, 7, BRAND if index == page else PANEL)


def title(text, note=""):
    """Clears the page and puts its heading top left, with an optional note on the right."""
    display.fill_rect(0, BODY, 240, 135 - BODY, BACKGROUND)
    label(text, 6, BODY)
    if note:
        label(note, 234 - len(note) * 8, BODY + 4, scale=1)


# --- The pages. Each draws itself once, then only what changed, so nothing flickers -------------

def temperature_page(draw, seconds, state):
    # Four readings a second: redrawing the number costs 40 ms, and a figure that changes twenty
    # times a second cannot be read anyway.
    seconds = int(seconds * 4) / 4
    reading = 21.5 + 5 * sin(seconds / 4) + 0.6 * sin(seconds * 1.3)
    if state["fahrenheit"]:
        shown = "%.1f°" % (reading * 9 / 5 + 32)
    else:
        shown = "%.1f°" % reading
    if draw:
        title("TEMPERATURE", "F" if state["fahrenheit"] else "C")
        label("%d" % CHART_LOW, BAR_X, 116, scale=1)
        label("%d C" % CHART_HIGH, BAR_X + BAR_WIDTH - 32, 116, scale=1)
        state["shown"] = None
    if shown != state.get("shown"):
        value(shown, 6, 60)
        bar(104, (reading - CHART_LOW) * 100 / (CHART_HIGH - CHART_LOW), BRAND)
        state["shown"] = shown


def chart_page(draw, seconds, state):
    reading = 21.5 + 5 * sin(seconds / 4) + 0.6 * sin(seconds * 1.3)
    if draw:
        title("LIVE TEMP", "%d-%d C" % (CHART_LOW, CHART_HIGH))
        display.blit_buffer(chart_pixels, CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT)
        return
    # Where the new reading sits, then slide the chart left and draw only the new columns.
    y = CHART_HEIGHT - 4 - int((reading - CHART_LOW) * (CHART_HEIGHT - 8) / (CHART_HIGH - CHART_LOW))
    y = max(2, min(y, CHART_HEIGHT - 4))
    was = state["y"]
    right = CHART_WIDTH - SCROLL
    chart.scroll(-SCROLL, 0)
    chart.fill_rect(right, 0, SCROLL, CHART_HEIGHT, INK_BACKGROUND)
    chart.hline(right, CHART_HEIGHT // 2, SCROLL, INK_GRID)
    for column in range(SCROLL):
        top = was + (y - was) * (column + 1) // SCROLL
        chart.vline(right + column, top, CHART_HEIGHT - top, INK_AREA)
    chart.line(right - 1, was, CHART_WIDTH - 1, y, INK_LINE)
    chart.line(right - 1, was + 1, CHART_WIDTH - 1, y + 1, INK_LINE)
    display.blit_buffer(chart_pixels, CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT)
    state["y"] = y


def buttons_page(draw, seconds, state):
    if draw:
        title("BUTTONS")
        label("LEFT", 6, 56, scale=1)
        label("RIGHT", 126, 56, scale=1)
        state["shown"] = None
    shown = (presses[0], presses[1])
    if shown != state.get("shown"):
        half(("%d" % presses[0], 6, BRAND), ("%d" % presses[1], 126, GOOD))
        bar(104, presses[0] % 100, BRAND)
        bar(116, presses[1] % 100, GOOD)
        state["shown"] = shown


PAGES = (temperature_page, chart_page, buttons_page)
state = [{"fahrenheit": False}, {"y": CHART_HEIGHT - 4}, {}]

chart.fill(INK_BACKGROUND)
chart.hline(0, CHART_HEIGHT // 2, CHART_WIDTH, INK_GRID)
display.fill(BACKGROUND)

page = 0
presses = [0, 0]
pressed = [False, False]
header()
dots(page)
draw = True
frame = 0
while True:
    start = ticks_ms()
    seconds = ticks_ms() / 1000

    # Act on the moment a button goes down, not on it being held.
    for index, button in enumerate(buttons):
        down = not button.value()
        if down and not pressed[index]:
            presses[index] += 1
            if index:
                page = (page + 1) % len(PAGES)   # right button: next page
                dots(page)
                draw = True
            else:
                # left button: whatever this page does with it
                state[0]["fahrenheit"] = not state[0]["fahrenheit"]
                draw = draw or page == 0
        pressed[index] = down

    PAGES[page](draw, seconds, state[page])
    draw = False

    elapsed = ticks_diff(ticks_ms(), start)
    if frame % 20 == 0:
        print("Frame: %d ms" % elapsed)
    sleep_ms(max(0, frame_ms - elapsed))
    frame += 1
