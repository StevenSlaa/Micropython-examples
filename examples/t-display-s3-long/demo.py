import framebuf
from machine import I2C, Pin
from math import sin
from time import sleep_ms, ticks_diff, ticks_ms
from axs15231b import AXS15231B, AXS15231BTouch, color565, WHITE
from sy6970 import SY6970
import pulsar_ui

# Configuration
# The display and touch are built into the board and wired to fixed pins, so there is nothing to choose.
# 1 or 3 is landscape, which the layout needs: 1 has the USB port on the right, 3 on the left
rotation = 1
# how long one frame lasts: 60 ms is about 16 frames a second, as fast as this dashboard can draw
frame_ms = 60
# set this to True if a LiPo battery is plugged into the board
battery = False

# The board's battery charger, an SY6970, shares this I2C bus with the touch. Its driver switches off
# the chip's watchdog, which otherwise resets its settings every 40 seconds. The chip also keeps trying
# to charge when no battery is connected, which froze the tested board after a few minutes, so charging
# is only on with a battery.
i2c = I2C(0, scl=Pin(10), sda=Pin(15), freq=400000)
charger = SY6970(i2c)
charger.charge_enabled = battery

display = AXS15231B(rotation=rotation)
touch = AXS15231BTouch(i2c, rotation=rotation)

# Colours
BACKGROUND = color565(12, 16, 28)
PANEL = color565(30, 36, 56)
MUTED = color565(140, 150, 175)
BRAND = color565(240, 64, 64)  # the red of "IoT" in the logo
AREA = color565(70, 26, 34)  # the same red, dimmed, under the chart line
WATER = color565(80, 160, 255)
GOOD = color565(60, 200, 110)
WARNING = color565(240, 190, 40)

# Layout of the 640x180 screen: three cards on the left, a chart on the right
CARDS = (6, 116, 226)  # left edge of each card
CARD_TOP, CARD_WIDTH, CARD_HEIGHT = 36, 104, 138
CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT = 338, 54, 296, 120
GRID = (0, CHART_HEIGHT // 2, CHART_HEIGHT - 1)
SCROLL = 2  # pixels the chart moves left every frame

# What each card shows: label, big number format, unit after it, small format, chart title, chart scale
READINGS = (
    ("TEMP", "%.1f°", "C", "%.1f C", "TEMPERATURE", 19, 24),
    ("HUMIDITY", "%d%%", "", "%d%%", "HUMIDITY", 40, 70),
    ("BATTERY", "%d%%", "", "%d%%", "BATTERY", 0, 100),
)

# The chart lives in memory: each frame it slides left with framebuf's scroll(), only the newest
# columns are drawn, and it goes to the screen in one blit, so it never shows half a frame.
chart_pixels = bytearray(CHART_WIDTH * CHART_HEIGHT * 2)
chart = framebuf.FrameBuffer(chart_pixels, CHART_WIDTH, CHART_HEIGHT, framebuf.RGB565)
# framebuf keeps a colour's two bytes the other way round from the display, so swap them once here
INK_BACKGROUND, INK_GRID, INK_AREA, INK_LINE = (((c & 0xFF) << 8) | (c >> 8) for c in (BACKGROUND, PANEL, AREA, BRAND))

# What each card shows right now, [number, bar length, bar colour, lowest, highest], so only changes are redrawn
shown = [["", 0, None, None, None] for _ in CARDS]
selected = 0


def big(text, x, y):
    """Draws `text` in the large Poppins characters from pulsar_ui.py and returns where it ends."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        display.bitmap(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, WHITE, PANEL)
        x += width
    return x


def draw_once():
    """Everything that never changes: the background, header and empty cards."""
    display.fill(BACKGROUND)
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        display.bitmap(bitmap, x, y, width, height, BRAND if colour == "RED" else WHITE, BACKGROUND)
    # the 1 bit swirl was made for e-paper; on this sharp screen the smooth colour icon replaces it
    display.blit_buffer(pulsar_ui.ICON, 4, 1, pulsar_ui.ICON_SIZE, pulsar_ui.ICON_SIZE)
    display.text("TAP A CARD TO CHART IT", 232, 11, MUTED, BACKGROUND)
    display.fill_rect(566, 5, 68, 17, PANEL)
    display.text("ONLINE", 584, 10, GOOD, PANEL)
    display.hline(0, 29, display.width, PANEL)
    for x, reading in zip(CARDS, READINGS):
        display.fill_rect(x, CARD_TOP, CARD_WIDTH, CARD_HEIGHT, PANEL)
        display.text(reading[0], x + 8, CARD_TOP + 10, MUTED, PANEL)


def select(index):
    """Outlines the chosen card in red and starts a fresh chart of its reading."""
    global selected, line_y
    for card_index, x in enumerate(CARDS):
        colour = BRAND if card_index == index else PANEL
        display.rect(x, CARD_TOP, CARD_WIDTH, CARD_HEIGHT, colour)
        display.rect(x + 1, CARD_TOP + 1, CARD_WIDTH - 2, CARD_HEIGHT - 2, colour)
    selected = index
    _, _, _, small, title, low, high = READINGS[index]
    display.fill_rect(CHART_X, 38, CHART_WIDTH, 8, BACKGROUND)
    display.text("LIVE " + title, CHART_X, 38, MUTED, BACKGROUND)
    scale = "%d-%d" % (low, high) + small[-1]
    display.text(scale, CHART_X + CHART_WIDTH - 8 * len(scale), 38, MUTED, BACKGROUND)
    chart.fill(INK_BACKGROUND)
    for y in GRID:
        chart.hline(0, y, CHART_WIDTH, INK_GRID)
    line_y = CHART_HEIGHT - 6  # the line starts at the bottom and climbs to the first reading


def card(index, value, percent, colour):
    """Updates a card's number, lowest and highest value and bar, drawing only what changed."""
    x = CARDS[index]
    state = shown[index]
    _, number, unit, small, _, _, _ = READINGS[index]
    text = number % value
    y = CARD_TOP + 30
    if text != state[0]:
        end = big(text, x + 8, y)
        # a shorter number than last time would leave old pixels behind, so paint the rest of the row
        display.fill_rect(end, y, x + CARD_WIDTH - 8 - end, pulsar_ui.FONT_HEIGHT, PANEL)
        if unit:
            display.text(unit, end + 1, y + 2, MUTED, PANEL)
        state[0] = text
    if state[3] is None or value < state[3]:
        state[3] = value
        display.text("%-11s" % ("MIN " + small % value), x + 8, CARD_TOP + 66, MUTED, PANEL)
    if state[4] is None or value > state[4]:
        state[4] = value
        display.text("%-11s" % ("MAX " + small % value), x + 8, CARD_TOP + 80, MUTED, PANEL)

    # the bar glides a quarter of the way to its new length each frame, at least one pixel
    old = state[1]
    track = CARD_WIDTH - 16
    target = track * max(0, min(percent, 100)) // 100
    new = old + ((target - old) // 4 or (target > old) - (target < old))
    left, top = x + 8, CARD_TOP + CARD_HEIGHT - 20
    if colour != state[2]:
        display.fill_rect(left, top, new, 6, colour)
    elif new > old:
        display.fill_rect(left + old, top, new - old, 6, colour)
    if new < old:
        display.fill_rect(left + new, top, old - new, 6, BACKGROUND)
    state[1], state[2] = new, colour


def chart_step(value):
    """Slides the chart left, draws the newest columns on the right and sends it to the screen."""
    global line_y
    low, high = READINGS[selected][5:]
    y = CHART_HEIGHT - 6 - int((value - low) * (CHART_HEIGHT - 10) / (high - low))
    y = max(3, min(y, CHART_HEIGHT - 6))
    right = CHART_WIDTH - SCROLL
    chart.scroll(-SCROLL, 0)
    chart.fill_rect(right, 0, SCROLL, CHART_HEIGHT, INK_BACKGROUND)
    for grid_y in GRID:
        chart.hline(right, grid_y, SCROLL, INK_GRID)
    for column in range(SCROLL):
        column_y = line_y + (y - line_y) * (column + 1) // SCROLL
        chart.vline(right + column, column_y, CHART_HEIGHT - 1 - column_y, INK_AREA)
    # the line is two pixels thick
    chart.line(right - 1, line_y, CHART_WIDTH - 1, y, INK_LINE)
    chart.line(right - 1, line_y + 1, CHART_WIDTH - 1, y + 1, INK_LINE)
    display.blit_buffer(chart_pixels, CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT)
    line_y = y


def status_light(seconds):
    """The light in the ONLINE label glows up and down, about once every one and a half seconds."""
    glow = (sin(seconds * 4) + 1) / 2
    display.fill_rect(572, 10, 6, 6, color565(int(30 + 30 * glow), int(36 + 164 * glow), int(56 + 54 * glow)))


def tapped(point):
    """A new touch: if it is on a card, chart that card's reading."""
    x, y = point
    for index, left in enumerate(CARDS):
        if left <= x < left + CARD_WIDTH and CARD_TOP <= y < CARD_TOP + CARD_HEIGHT and index != selected:
            select(index)


draw_once()
select(0)
frame = 0
touching = None
while True:
    start = ticks_ms()
    seconds = frame * frame_ms / 1000

    # Illustrative readings. Nothing is measured: this is a picture of what a dashboard could show.
    temperature = 21.5 + 1.5 * sin(seconds / 4) + 0.4 * sin(seconds * 1.3)
    humidity = 55 + 5 * sin(seconds / 7) + 2 * sin(seconds * 0.9)
    battery = 100 - int(seconds / 2) % 96  # drains 1% every 2 seconds, then starts again

    card(0, temperature, int((temperature - 15) * 100 / 15), BRAND)
    card(1, humidity, int(humidity), WATER)
    card(2, battery, battery, GOOD if battery > 50 else WARNING if battery > 20 else BRAND)
    chart_step((temperature, humidity, battery)[selected])
    status_light(seconds)

    # only the moment a finger comes down counts as a tap, not holding it there
    point = touch.read()
    if point and not touching:
        tapped(point)
    touching = point

    elapsed = ticks_diff(ticks_ms(), start)
    if frame % 16 == 0:
        print("Frame: %d ms" % elapsed)
    sleep_ms(max(0, frame_ms - elapsed))
    frame += 1
