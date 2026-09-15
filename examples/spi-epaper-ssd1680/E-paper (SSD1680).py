import os, sys
from machine import Pin, SPI
from time import sleep, ticks_diff, ticks_ms
from ssd1680 import SSD1680, WHITE, BLACK, RED
import pulsar_ui

# Configuration
# pins for each board: SPI bus, SCL (SCK), SDA (MOSI), CS, D/C, RES, BUSY (GPIO numbers)
pins = {
    "pico": (1, 10, 11, 13, 14, 15, 12),
    "xiao-rp2040": (0, 2, 3, 7, 0, 1, 4),
    "esp32": (2, 18, 23, 5, 17, 16, 4),
    "esp32s3": (2, 12, 11, 10, 9, 8, 7),
}
# the board is recognised by itself, except a Seeed XIAO RP2040: it runs the same firmware as a
# Pico. On a XIAO, remove the # in front of the last line below
if sys.platform == "rp2":
    board = "pico"
elif "ESP32S3" in os.uname().machine:
    board = "esp32s3"
else:
    board = "esp32"
# board = "xiao-rp2040"
spi_id, sck_pin, mosi_pin, cs_pin, dc_pin, rst_pin, busy_pin = pins[board]
# 270 or 90 is landscape, which the layout needs. If the picture is upside down, use the other one
rotation = 270
# three colour e-paper should not be refreshed more often than every 3 minutes
refresh_minutes = 3

spi = SPI(spi_id, baudrate=4000000, sck=Pin(sck_pin), mosi=Pin(mosi_pin))
display = SSD1680(spi, cs=Pin(cs_pin), dc=Pin(dc_pin), rst=Pin(rst_pin), busy=Pin(busy_pin),
                  rotation=rotation)

# Illustrative readings. Nothing is measured: this is a picture of what a dashboard could show.
temperature = 21.4
humidity = 58
battery = 87
history = [18.9, 18.6, 18.4, 18.2, 18.1, 18.3, 18.9, 19.6, 20.4, 21.1, 21.8, 22.3,
           22.6, 22.8, 22.7, 22.4, 22.0, 21.6, 21.3, 21.1, 21.0, 21.2, 21.3, 21.4]


def big(text, x, y):
    """Draws `text` in the large Poppins characters from pulsar_ui.py and returns where it ends."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        display.bitmap(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, BLACK)
        x += width
    return x


def card(x, label):
    """An outlined card, 94 pixels wide, with a small label at the top."""
    display.rect(x, 30, 94, 58, BLACK)
    display.text(label, x + 6, 36, BLACK)


def draw():
    display.fill(WHITE)

    # Header: the logo, a status label, and a line underneath.
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        display.bitmap(bitmap, x, y, width, height, RED if colour == "RED" else BLACK)
    display.rect(238, 6, 54, 14, RED, fill=True)
    display.text("ONLINE", 241, 9, WHITE)
    display.hline(0, 26, display.width, BLACK)

    # Three cards with the latest readings.
    card(4, "TEMP")
    end = big("%.1f°" % temperature, 10, 54)
    display.text("C", end + 1, 56, BLACK)
    card(101, "HUMIDITY")
    big("%d%%" % humidity, 107, 54)
    card(198, "BATTERY")
    big("%d%%" % battery, 204, 54)
    # a battery symbol beside the label, with the fill turning red when it runs low
    display.rect(266, 35, 20, 10, BLACK)
    display.vline(286, 38, 4, BLACK)
    display.rect(268, 37, 16 * battery // 100, 6, RED if battery < 20 else BLACK, fill=True)

    # A chart of the last 24 hours, with the latest reading as a red dot.
    low, high = min(history), max(history)
    display.text("LAST 24 HOURS", 4, 93, BLACK)
    span = "%.1f-%.1f C" % (low, high)
    display.text(span, display.width - 4 - 8 * len(span), 93, BLACK)
    display.hline(4, 126, display.width - 8, BLACK)
    points = []
    for index, value in enumerate(history):
        x = 4 + index * (display.width - 9) // (len(history) - 1)
        y = 124 - round((value - low) * 18 / ((high - low) or 1))
        points.append((x, y))
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        display.line(x1, y1, x2, y2, BLACK)
        display.line(x1, y1 - 1, x2, y2 - 1, BLACK)  # two pixels thick reads better on e-paper
    display.ellipse(points[-1][0], points[-1][1], 3, 3, RED, fill=True)


update = 0
while True:
    update += 1
    draw()

    print("Refreshing, the screen will flash for about 25 seconds...")
    start = ticks_ms()
    display.show()
    print("Refresh: %.1f s" % (ticks_diff(ticks_ms(), start) / 1000))

    sleep(refresh_minutes * 60)

    # Illustrative only: nudge the numbers, so every refresh shows the dashboard changing.
    temperature = round(temperature + (0.3, -0.2, 0.1)[update % 3], 1)
    humidity += (1, -2, 1)[update % 3]
    battery = max(battery - 1, 0)
    history = history[1:] + [temperature]
