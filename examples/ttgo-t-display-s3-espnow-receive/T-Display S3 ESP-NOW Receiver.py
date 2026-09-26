import espnow
import framebuf
import network
from machine import Pin
from math import sin
from time import sleep_ms, ticks_diff, ticks_ms
from st7789_parallel import ST7789Parallel, color565, WHITE
import pulsar_ui

# Configuration
# 1 to 13. Both boards must be on the same wifi channel.
channel = 1
# no message for this long and the link counts as lost
link_timeout_ms = 3000
# how long one frame lasts: 50 ms is 20 frames a second
frame_ms = 50
# 1 or 3 is landscape, which the layout needs. If the picture is upside down, use the other one
rotation = 1

# GPIO 15 powers the board's peripherals: it must be high before the display is set up
Pin(15, Pin.OUT, value=1)
display = ST7789Parallel(
    [Pin(pin, Pin.OUT) for pin in (39, 40, 41, 42, 45, 46, 47, 48)],  # LCD D0 through D7
    wr=Pin(8, Pin.OUT), dc=Pin(7, Pin.OUT), cs=Pin(6, Pin.OUT), reset=Pin(5, Pin.OUT),
    rd=Pin(9, Pin.OUT), backlight=Pin(38, Pin.OUT),
    rotation=rotation,
    fast=True,  # direct ESP32-S3 register writes, only for this board's LCD pins
)

# ESP-NOW uses the wifi radio, so the station interface must be on. It does not connect anywhere.
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=channel)
esp = espnow.ESPNow()
esp.active(True)

my_mac = sta.config("mac")
print("My address:", my_mac.hex(":"))
print('Sender setting: receiver = b"' + "".join("\\x%02x" % b for b in my_mac) + '"')

# Colours
BACKGROUND = color565(12, 16, 28)
PANEL = color565(30, 36, 56)
MUTED = color565(140, 150, 175)
BRAND = color565(240, 64, 64)  # the red of "IoT" in the logo
WATER = color565(80, 160, 255)
GOOD = color565(60, 200, 110)
WARNING = color565(240, 190, 40)

# Layout of the 320x170 screen
CARDS = (6, 111, 216)  # left edge of each card
CARD_TOP, CARD_WIDTH, CARD_HEIGHT = 34, 98, 60
CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT = 6, 112, 308, 40
RSSI_LOW, RSSI_HIGH = -95, -35  # the chart's scale in dBm, fixed because it scrolls
GRID = (0, CHART_HEIGHT // 2, CHART_HEIGHT - 1)
FOOTER_Y = 158
PILL_X = 236

# The signal chart lives in memory and slides left one pixel a frame, like the T-Display S3 dashboard
chart_pixels = bytearray(CHART_WIDTH * CHART_HEIGHT * 2)
chart = framebuf.FrameBuffer(chart_pixels, CHART_WIDTH, CHART_HEIGHT, framebuf.RGB565)
# framebuf keeps a colour's two bytes the other way round from the display, so swap them once here
INK_BACKGROUND, INK_GRID, INK_AREA, INK_LINE, INK_MISSED = (
    ((c & 0xFF) << 8) | (c >> 8) for c in (BACKGROUND, PANEL, color565(20, 48, 90), WATER, BRAND))

# What is on screen right now, so only changes are redrawn: [number, bar length, bar colour] per card
shown = {x: ["", 0, None] for x in CARDS}
shown_text = {}


def big(text, x, y):
    """Draws `text` in the large Poppins characters from pulsar_ui.py and returns where it ends."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        display.bitmap(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, WHITE, PANEL)
        x += width
    return x


def small(key, text, x, y, colour, background):
    """Draws a line of 8x8 text, but only when it changed since last time."""
    if shown_text.get(key) != (text, colour):
        display.text(text, x, y, colour, background)
        shown_text[key] = (text, colour)


def draw_once():
    """Everything that never changes: the background, header, empty cards and labels."""
    display.fill(BACKGROUND)
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        display.bitmap(bitmap, x, y, width, height, BRAND if colour == "RED" else WHITE, BACKGROUND)
    display.fill_rect(PILL_X, 5, display.width - 6 - PILL_X, 17, PANEL)
    display.hline(0, 28, display.width, PANEL)
    for x, label in zip(CARDS, ("RECEIVED", "DELIVERY", "SIGNAL")):
        display.fill_rect(x, CARD_TOP, CARD_WIDTH, CARD_HEIGHT, PANEL)
        display.text(label, x + 6, CARD_TOP + 6, MUTED, PANEL)
    display.text("ESP-NOW SIGNAL", CHART_X, 100, MUTED, BACKGROUND)
    scale = "CH %d  %d..%d dBm" % (channel, RSSI_LOW, RSSI_HIGH)
    display.text(scale, display.width - 6 - 8 * len(scale), 100, MUTED, BACKGROUND)
    chart.fill(INK_BACKGROUND)
    for y in GRID:
        chart.hline(0, y, CHART_WIDTH, INK_GRID)


def card(x, value, unit, percent, colour):
    """Updates a card's number and bar, drawing only what changed, so nothing flickers."""
    state = shown[x]
    y = CARD_TOP + 22
    if value != state[0]:
        # ponytail: 5 digits fit a card, about 27 hours of messages at one a second
        end = big(value, x + 6, y)
        # a shorter number than last time would leave old pixels behind, so paint the rest of the row
        display.fill_rect(end, y, max(0, x + CARD_WIDTH - 6 - end), pulsar_ui.FONT_HEIGHT, PANEL)
        if unit:
            display.text(unit, end + 2, y + 10, MUTED, PANEL)
        state[0] = value
    if percent is None:
        return

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


def chart_step(rssi, last_y, missed_marker):
    """Slides the chart left and draws the newest column: the signal, a gap, or a red missed mark."""
    right = CHART_WIDTH - 1
    chart.scroll(-1, 0)
    chart.vline(right, 0, CHART_HEIGHT, INK_MISSED if missed_marker else INK_BACKGROUND)
    y = None
    if not missed_marker:
        for grid_y in GRID:
            chart.pixel(right, grid_y, INK_GRID)
        if rssi is not None:
            y = CHART_HEIGHT - 3 - (rssi - RSSI_LOW) * (CHART_HEIGHT - 6) // (RSSI_HIGH - RSSI_LOW)
            y = max(2, min(y, CHART_HEIGHT - 3))
            chart.vline(right, y, CHART_HEIGHT - y, INK_AREA)
            start = y if last_y is None else last_y
            # the line is two pixels thick
            chart.line(right - 1, start, right, y, INK_LINE)
            chart.line(right - 1, start + 1, right, y + 1, INK_LINE)
    display.blit_buffer(chart_pixels, CHART_X, CHART_Y, CHART_WIDTH, CHART_HEIGHT)
    return y


def mix(dim, bright, amount):
    """A colour between two RGB tuples, 0 is `dim` and 1 is `bright`."""
    return color565(*(int(d + (b - d) * amount) for d, b in zip(dim, bright)))


def status(state, flash, seconds):
    """The pill in the top right: its light flashes on every message and its label names the state."""
    if state == "LINKED":
        colour, light = GOOD, mix((20, 90, 50), (140, 255, 170), flash)
    elif state == "NO LINK":
        colour, light = BRAND, (BRAND if int(seconds * 2) % 2 else PANEL)
    else:  # waiting for the first message: a slow amber glow
        colour, light = WARNING, mix((60, 50, 20), (240, 190, 40), (sin(seconds * 3) + 1) / 2)
    display.fill_rect(PILL_X + 6, 10, 6, 6, light)
    small("state", "%-7s" % state, PILL_X + 18, 10, colour, PANEL)


def signal_colour(rssi):
    return GOOD if rssi > -67 else WARNING if rssi > -80 else BRAND


# One sender at a time, like the sending example: its counter goes up by one each message
received = counted = missed = 0
expected = sender = rssi = last_ms = line_y = None
flash = 0.0

draw_once()
frame = 0
while True:
    start = ticks_ms()
    seconds = frame * frame_ms / 1000

    missed_before = missed
    while esp.any():
        mac, msg = esp.recv(0)
        if msg is None:
            break
        received += 1
        sender, last_ms, flash = mac, start, 1.0
        rssi = esp.peers_table[mac][0]
        # messages come from the air, so anything that is not a counter is shown but not checked for gaps
        try:
            counter = int(msg)
        except ValueError:
            continue
        counted += 1
        # a gap means messages were lost; a lower counter means the sender restarted, which is not a loss
        if expected is not None and counter > expected:
            missed += counter - expected
        expected = counter + 1
        print("RSSI: %d dBm  Missed: %d" % (rssi, missed))

    age = None if last_ms is None else ticks_diff(start, last_ms)
    state = "WAITING" if age is None else "LINKED" if age < link_timeout_ms else "NO LINK"
    linked = state == "LINKED"

    card(CARDS[0], "%d" % received, "", None, None)
    small("missed", "MISSED %-5d" % missed, CARDS[0] + 6, CARD_TOP + 48, BRAND if missed else MUTED, PANEL)
    if counted:
        # floor, so 100% only shows when nothing at all was lost
        delivery = 100 * counted // (counted + missed)
        card(CARDS[1], "%d%%" % delivery, "", delivery,
             GOOD if delivery >= 95 else WARNING if delivery >= 80 else BRAND)
    else:
        card(CARDS[1], "--", "", 0, MUTED)
    if linked:
        card(CARDS[2], "%d" % rssi, "dBm", (rssi + 90) * 2, signal_colour(rssi))
    else:
        card(CARDS[2], "--", "dBm", 0, MUTED)

    line_y = chart_step(rssi if linked else None, line_y, missed > missed_before)
    status(state, flash, seconds)
    flash *= 0.75

    # the footer names the sender, or this board's own address while there is none yet to copy it from
    if sender is None:
        left, right = "MY MAC " + my_mac.hex(":"), "LISTENING"
    else:
        left, right = "FROM " + sender.hex(":"), "%.1fs AGO" % (age / 1000)
    footer = left + " " * max(1, 38 - len(left) - len(right)) + right
    small("footer", footer, 6, FOOTER_Y, WHITE if linked else MUTED, BACKGROUND)

    elapsed = ticks_diff(ticks_ms(), start)
    sleep_ms(max(0, frame_ms - elapsed))
    frame += 1
