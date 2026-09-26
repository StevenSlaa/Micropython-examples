import espnow
import framebuf
import machine
import network
from machine import Pin, SPI
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms
import st7789py as st7789
from st7789py import color565
import pulsar_ui

# Configuration
# The receiving board shows its address on screen and prints it when it starts; paste it here. The
# default is the broadcast address, which reaches every ESP-NOW board in range but is never
# acknowledged, so the delivery rate can only be measured with a real address.
receiver = b"\xff\xff\xff\xff\xff\xff"
# 1 to 13. Both boards must be on the same wifi channel.
channel = 1
# the right button steps through these, in milliseconds between messages
intervals = (1000, 500, 250)
# The display and both buttons are built into the board, so there is nothing to wire or choose.
lcd_sck, lcd_mosi, lcd_cs, lcd_dc, lcd_res, lcd_bl = 18, 19, 5, 16, 23, 4
button_left, button_right = 0, 35
# 1 or 3 is landscape (240x135), which the layout needs. Upside down? Use the other one.
rotation = 1
# the fastest this board's SPI bus runs through the GPIO matrix; more crashes it
baudrate = 26666666
# how long one frame lasts: 50 ms is 20 frames a second
frame_ms = 50

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
WATER = color565(80, 160, 255)
GOOD = color565(60, 200, 110)
WARNING = color565(240, 190, 40)

# Layout of the 240x135 screen
HEADER = 28
STATUS_X = 160
STRIP_X, STRIP_Y, STRIP_WIDTH, STRIP_HEIGHT = 6, 88, 228, 10
CELL = 6  # one message in the strip: 5 pixels and a gap
FOOTER_Y = 110

# The last 38 messages as a strip of squares, kept in memory: each send slides it left one square
# and it goes to the screen in one blit. framebuf keeps a colour's two bytes the other way round.
strip_pixels = bytearray(STRIP_WIDTH * STRIP_HEIGHT * 2)
strip = framebuf.FrameBuffer(strip_pixels, STRIP_WIDTH, STRIP_HEIGHT, framebuf.RGB565)


def swapped(colour):
    """framebuf keeps a colour's two bytes the other way round from the display."""
    return ((colour & 0xFF) << 8) | (colour >> 8)


_luts = {}
# One buffer every label and bitmap is drawn through, big enough for the logo or a 30 character line
_pixels = bytearray(max(max(len(part[-1]) for part in pulsar_ui.LOGO), 30 * 8) * 16)


def lut_for(colour, background):
    """
    A 4 KB table turning one byte of a 1 bit bitmap into its 8 pixels, 16 bytes at byte * 16.

    Expanding a byte at a time is about ten times quicker than a pixel at a time. The table is one
    bytearray rather than 256 small objects, which would take twice the memory and scatter it.
    """
    lut = _luts.get((colour, background))
    if lut is None:
        ink = bytes((colour >> 8, colour & 0xFF))
        paper = bytes((background >> 8, background & 0xFF))
        lut = bytearray(4096)
        for byte in range(256):
            for bit in range(8):
                at = byte * 16 + bit * 2
                lut[at:at + 2] = ink if byte & 128 >> bit else paper
        _luts[(colour, background)] = memoryview(lut)
    return _luts[(colour, background)]


def mono(bitmap, x, y, width, height, colour, background=BACKGROUND):
    """Draws a 1 bit MONO_HLSB bitmap in two colours, a byte at a time through the table."""
    lut = lut_for(colour, background)
    at = 0
    for byte in bitmap:
        _pixels[at:at + 16] = lut[byte * 16:byte * 16 + 16]
        at += 16
    # A bitmap's rows are whole bytes, so the drawn width is rounded up to the next multiple of 8.
    display.blit_buffer(memoryview(_pixels)[:at], x, y, (width + 7) // 8 * 8, height)


def label(text, x, y, colour=MUTED):
    """Draws text in framebuf's built in 8x8 font."""
    width = len(text) * 8
    characters = bytearray(len(text) * 8)
    framebuf.FrameBuffer(characters, width, 8, framebuf.MONO_HLSB).text(text, 0, 0, 1)
    mono(characters, x, y, width, 8, colour)


def value(text, x, y, until):
    """Draws a number in the large Poppins characters and wipes whatever a longer number left behind."""
    for character in text:
        width, bitmap = pulsar_ui.FONT[character]
        mono(bitmap, x, y, width, pulsar_ui.FONT_HEIGHT, st7789.WHITE)
        x += width
    display.fill_rect(x, y, max(0, until - x), pulsar_ui.FONT_HEIGHT, BACKGROUND)


def footer(left, right, y):
    """One line of small text with a part on the left and a part on the right, 30 characters wide."""
    label(left + " " * max(1, 30 - len(left) - len(right)) + right, 0, y, MUTED)


def draw_once():
    """Everything that never changes: the background, logo, labels and the empty strip."""
    display.fill(BACKGROUND)
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        mono(bitmap, x, y, width, height, BRAND if colour == "RED" else st7789.WHITE)
    display.hline(0, HEADER, 240, PANEL)
    label("SENT", 6, 34)
    label("DELIVERY", 126, 34)
    label("LAST %d MESSAGES" % (STRIP_WIDTH // CELL), 6, 76)
    display.hline(0, FOOTER_Y - 6, 240, PANEL)
    footer("TO " + ("EVERYONE" if broadcast else receiver.hex(":")), "", FOOTER_Y)
    strip.fill(swapped(BACKGROUND))
    for x in range(0, STRIP_WIDTH, CELL):
        strip.fill_rect(x, 0, CELL - 1, STRIP_HEIGHT, swapped(PANEL))
    display.blit_buffer(strip_pixels, STRIP_X, STRIP_Y, STRIP_WIDTH, STRIP_HEIGHT)


def add_to_strip(colour):
    """Slides the strip one square to the left and puts the newest message on the right."""
    strip.scroll(-CELL, 0)
    strip.fill_rect(STRIP_WIDTH - CELL, 0, CELL - 1, STRIP_HEIGHT, swapped(colour))
    display.blit_buffer(strip_pixels, STRIP_X, STRIP_Y, STRIP_WIDTH, STRIP_HEIGHT)


def mix(dim, bright, amount):
    """A colour between two RGB tuples, 0 is `dim` and 1 is `bright`."""
    return color565(*(int(d + (b - d) * amount) for d, b in zip(dim, bright)))


shown_status = None


def status(text, colour, light):
    """The light and the word in the top right. The word is only redrawn when it changes."""
    global shown_status
    display.fill_rect(STATUS_X, 11, 7, 7, light)
    if (text, colour) != shown_status:
        label("%-7s" % text, STATUS_X + 12, 11, colour)
        shown_status = (text, colour)


# Every table and buffer is made now, while the heap is still in one piece: wifi takes a large part
# of this board's memory, and 4 KB in one block is hard to find once the program has been running.
for colour in (st7789.WHITE, MUTED, BRAND, GOOD, WATER, WARNING):
    lut_for(colour, BACKGROUND)

# ESP-NOW uses the wifi radio, so the station interface must be on. It does not connect anywhere.
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=channel)
esp = espnow.ESPNow()
esp.active(True)
esp.add_peer(receiver)
broadcast = receiver == b"\xff" * 6
print("Sending on channel", channel, "to", "everyone" if broadcast else receiver.hex(":"))

draw_once()
sent = delivered = 0
last_ok = True
paused = False
interval = 0  # index into intervals
pressed = [False, False]
flash = 0.0
next_send = ticks_ms()
redraw = True
while True:
    start = ticks_ms()

    # Act on the moment a button goes down, not on it being held.
    for index, button in enumerate(buttons):
        down = not button.value()
        if down and not pressed[index]:
            if index == 0:
                paused = not paused  # left button: pause or resume sending
            else:
                interval = (interval + 1) % len(intervals)  # right button: the next rate
            next_send = start
            redraw = True
        pressed[index] = down

    if not paused and ticks_diff(start, next_send) >= 0:
        next_send = ticks_add(next_send, intervals[interval])
        if ticks_diff(start, next_send) >= 0:  # fell behind, perhaps after a pause: don't catch up in a burst
            next_send = ticks_add(start, intervals[interval])
        sent += 1
        # send() returns True when the other board's radio acknowledged the message, after the radio
        # has retried a few times itself. A broadcast is never acknowledged: True only means it left.
        last_ok = esp.send(receiver, str(sent))
        delivered += last_ok
        flash = 1.0
        add_to_strip(WATER if broadcast else GOOD if last_ok else BRAND)
        print("Sent: %d  Delivered: %d  Lost: %d" % (sent, delivered, sent - delivered))
        redraw = True

    if redraw:
        value("%d" % sent, 6, 46, 120)
        if broadcast or not sent:
            value("--", 126, 46, 234)
        else:
            # floor, so 100% only shows when nothing at all was lost
            value("%d%%" % (100 * delivered // sent), 126, 46, 234)
        lost = "BROADCAST" if broadcast else "LOST %d" % (sent - delivered)
        footer(lost, "CH %d  EVERY %dms" % (channel, intervals[interval]), FOOTER_Y + 14)
        redraw = False

    if paused:
        status("PAUSED", WARNING, WARNING)
    elif broadcast:
        status("BCAST", WATER, mix((20, 40, 70), (150, 210, 255), flash))
    elif last_ok:
        status("SENDING", GOOD, mix((20, 90, 50), (140, 255, 170), flash))
    else:
        status("NO ACK", BRAND, mix((70, 20, 20), (255, 110, 110), flash))
    flash *= 0.7

    sleep_ms(max(0, frame_ms - ticks_diff(ticks_ms(), start)))
