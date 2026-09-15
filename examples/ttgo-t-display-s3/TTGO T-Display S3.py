import framebuf
from machine import Pin
from math import sin
from time import sleep_ms, ticks_diff, ticks_ms
from st7789_parallel import ST7789Parallel, color565, WHITE
import pulsar_ui

# Configuration
# The display is built into the board and wired to fixed pins, so there is nothing to choose here.
# GPIO 15 powers the board's peripherals: it must be high before the display is set up
Pin(15, Pin.OUT, value=1)
# 1 or 3 is landscape, which the layout needs. If the picture is upside down, use the other one
rotation = 1
# how long one frame lasts: 40 ms is 25 frames a second
frame_ms = 40

display = ST7789Parallel(
    [Pin(pin, Pin.OUT) for pin in (39, 40, 41, 42, 45, 46, 47, 48)],  # LCD D0 through D7
    wr=Pin(8, Pin.OUT), dc=Pin(7, Pin.OUT), cs=Pin(6, Pin.OUT), reset=Pin(5, Pin.OUT),
    rd=Pin(9, Pin.OUT), backlight=Pin(38, Pin.OUT),
    rotation=rotation,
    fast=True,  # direct ESP32-S3 register writes, only for this board's LCD pins
)

# Colours
BACKGROUND = color565(12, 16, 28)
PANEL = color565(30, 36, 56)
MUTED = color565(140, 150, 175)
BRAND = color565(240, 64, 64)  # the red of "IoT" in the logo
AREA = color565(70, 26, 34)  # the same red, dimmed, under the chart line
WATER = color565(80, 160, 255)
GOOD = color565(60, 200, 110)
WARNING = color565(240, 190, 40)

# Layout of the 320x170 screen
CARDS = (6, 111, 216)  # left edge of each card
CARD_TOP, CARD_WIDTH, CARD_HEIGHT = 34, 98, 60
CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT = 6, 112, 308, 54
CHART_LOW, CHART_HIGH = 19, 24  # the chart's scale in °C, fixed because it scrolls
GRID = (0, CHART_HEIGHT // 2, CHART_HEIGHT - 1)
SCROLL = 2  # pixels the chart moves left every frame

# The chart lives in memory: each frame it slides left with framebuf's fast scroll(), only the new
# columns on the right are drawn, and the whole chart goes to the screen in one blit, so it never
# shows half a frame. It needs only its own 308x54 area: 33 KB, not the whole screen.
chart_pixels = bytearray(CHART_WIDTH * CHART_HEIGHT * 2)
chart = framebuf.FrameBuffer(chart_pixels, CHART_WIDTH, CHART_HEIGHT, framebuf.RGB565)
# framebuf keeps a colour's two bytes the other way round from the display, so swap them once here
INK_BACKGROUND, INK_GRID, INK_AREA, INK_LINE = (((c & 0xFF) << 8) | (c >> 8) for c in (BACKGROUND, PANEL, AREA, BRAND))

# What each card shows right now, [number, bar length, bar colour], so only changes are redrawn
shown = {x: ["", 0, None] for x in CARDS}


def big(text, x, y):
    """Draws `text` in the large Poppins characters from pulsar_ui.py and returns where it ends."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        display.bitmap(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, WHITE, PANEL)
        x += width
    return x


def draw_once():
    """Everything that never changes: the background, header, empty cards and labels."""
    display.fill(BACKGROUND)
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        display.bitmap(bitmap, x, y, width, height, BRAND if colour == "RED" else WHITE, BACKGROUND)
    display.fill_rect(248, 5, 66, 17, PANEL)
    display.text("ONLINE", 264, 10, GOOD, PANEL)
    display.hline(0, 28, display.width, PANEL)
    for x, label in zip(CARDS, ("TEMP", "HUMIDITY", "BATTERY")):
        display.fill_rect(x, CARD_TOP, CARD_WIDTH, CARD_HEIGHT, PANEL)
        display.text(label, x + 6, CARD_TOP + 6, MUTED, PANEL)
    display.text("LIVE TEMPERATURE", CHART_X, 100, MUTED, BACKGROUND)
    scale = "%d-%d C" % (CHART_LOW, CHART_HIGH)
    display.text(scale, display.width - 6 - 8 * len(scale), 100, MUTED, BACKGROUND)
    chart.fill(INK_BACKGROUND)
    for y in GRID:
        chart.hline(0, y, CHART_WIDTH, INK_GRID)


def card(x, value, unit, percent, colour):
    """Updates a card's number and bar, drawing only what changed, so nothing flickers."""
    state = shown[x]
    y = CARD_TOP + 22
    if value != state[0]:
        end = big(value, x + 6, y)
        # a shorter number than last time would leave old pixels behind, so paint the rest of the row
        display.fill_rect(end, y, x + CARD_WIDTH - 6 - end, pulsar_ui.FONT_HEIGHT, PANEL)
        if unit:
            display.text(unit, end + 1, y + 2, MUTED, PANEL)
        state[0] = value

    # the bar glides a quarter of the way to its new length each frame, at least one pixel
    old = state[1]
    target = (CARD_WIDTH - 12) * max(0, min(percent, 100)) // 100
    new = old + ((target - old) // 4 or (target > old) - (target < old))
    left, top = x + 6, CARD_TOP + 50
    if colour != state[2]:
        display.fill_rect(left, top, new, 4, colour)
    elif new > old:
        display.fill_rect(left + old, top, new - old, 4, colour)
    if new < old:
        display.fill_rect(left + new, top, old - new, 4, BACKGROUND)
    state[1], state[2] = new, colour


def chart_step(value, last_y):
    """Slides the chart left, draws the newest columns on the right, and returns the line's height."""
    y = CHART_HEIGHT - 6 - int((value - CHART_LOW) * (CHART_HEIGHT - 10) / (CHART_HIGH - CHART_LOW))
    y = max(3, min(y, CHART_HEIGHT - 6))
    right = CHART_WIDTH - SCROLL
    chart.scroll(-SCROLL, 0)
    chart.fill_rect(right, 0, SCROLL, CHART_HEIGHT, INK_BACKGROUND)
    for grid_y in GRID:
        chart.hline(right, grid_y, SCROLL, INK_GRID)
    for column in range(SCROLL):
        column_y = last_y + (y - last_y) * (column + 1) // SCROLL
        chart.vline(right + column, column_y, CHART_HEIGHT - 1 - column_y, INK_AREA)
    # the line is two pixels thick
    chart.line(right - 1, last_y, CHART_WIDTH - 1, y, INK_LINE)
    chart.line(right - 1, last_y + 1, CHART_WIDTH - 1, y + 1, INK_LINE)
    display.blit_buffer(chart_pixels, CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT)
    return y


def status_light(seconds):
    """The light in the ONLINE label glows up and down, about once every one and a half seconds."""
    glow = (sin(seconds * 4) + 1) / 2
    display.fill_rect(254, 10, 6, 6, color565(int(30 + 30 * glow), int(36 + 164 * glow), int(56 + 54 * glow)))


draw_once()
frame = 0
line_y = CHART_HEIGHT - 6  # the line starts at the bottom and climbs to the first reading
while True:
    start = ticks_ms()
    seconds = frame * frame_ms / 1000

    # Illustrative readings. Nothing is measured: this is a picture of what a dashboard could show.
    temperature = 21.5 + 1.5 * sin(seconds / 4) + 0.4 * sin(seconds * 1.3)
    humidity = 55 + round(5 * sin(seconds / 7))
    battery = 100 - int(seconds / 2) % 96  # drains 1% every 2 seconds, then starts again

    card(CARDS[0], "%.1f°" % temperature, "C", int((temperature - 15) * 100 / 15), BRAND)
    card(CARDS[1], "%d%%" % humidity, "", humidity, WATER)
    card(CARDS[2], "%d%%" % battery, "", battery, GOOD if battery > 50 else WARNING if battery > 20 else BRAND)
    line_y = chart_step(temperature, line_y)
    status_light(seconds)

    elapsed = ticks_diff(ticks_ms(), start)
    if frame % 25 == 0:
        print("Frame: %d ms" % elapsed)
    sleep_ms(max(0, frame_ms - elapsed))
    frame += 1
