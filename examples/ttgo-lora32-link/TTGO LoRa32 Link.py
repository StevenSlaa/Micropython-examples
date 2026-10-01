from machine import ADC, I2C, Pin, SDCard, SPI, unique_id
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms
from struct import pack, unpack
from math import cos, sin
from os import urandom
import framebuf
import os
from sx127x import SX127x
from ssd1306 import SSD1306_I2C

# --- Settings: both boards run this same script, so these match by themselves -----------------
# In Hz: 868MHz in Europe, 915MHz in the Americas and Australia, 433MHz for SX1278 boards.
frequency = 868_000_000

# SF7 keeps each packet around 40ms on air, so a beacon every few seconds stays inside Europe's
# 1% rule. Raise it for range, and raise interval_ms with it: each step doubles the airtime.
spreading_factor = 7
bandwidth = 125_000

# dBm. 14 is the legal limit on the European channels.
tx_power = 14

# Each board sends a beacon this often, give or take a second so the two do not keep colliding.
interval_ms = 5000

# No beacon for this long and the link counts as lost.
lost_after_ms = 20_000

# The battery sits behind a divider that halves it. Trim this against a multimeter.
battery_scale = 2.0
# ---------------------------------------------------------------------------------------------

# LilyGO T3 LoRa32 V1.6.1: everything below is wired on the board.
lora = SX127x(SPI(1, baudrate=5_000_000, sck=Pin(5), mosi=Pin(27), miso=Pin(19)),
              cs=Pin(18), reset=Pin(23), frequency=frequency, bandwidth=bandwidth,
              spreading_factor=spreading_factor, tx_power=tx_power)
display = SSD1306_I2C(128, 64, I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000))
led = Pin(25, Pin.OUT, value=0)
battery = ADC(Pin(35), atten=ADC.ATTN_11DB)
# The card slot has its own pins, on the second SPI controller (slot 3); the radio has the first.
try:
    sd = SDCard(slot=3, sck=Pin(14), mosi=Pin(15), miso=Pin(2), cs=Pin(13))
except (OSError, ValueError):
    sd = None  # everything else still works without it

# Every ESP32 has a unique ID, so the two boards tell themselves apart without any setup.
me = int.from_bytes(unique_id()[-2:], "big")
MAGIC = b"T3"
LOG = "/sd/lora_link.csv"

# --- Drawing -----------------------------------------------------------------------------------
_glyph_buffer = bytearray(8)
_glyph = framebuf.FrameBuffer(_glyph_buffer, 8, 8, framebuf.MONO_HLSB)


def big(text, x, y, scale):
    """The built-in 8x8 font, blown up `scale` times: one character at a time, pixel by pixel."""
    for char in text:
        _glyph.fill(0)
        _glyph.text(char, 0, 0, 1)
        for row in range(8):
            bits = _glyph_buffer[row]
            for col in range(8):
                if bits & (0x80 >> col):
                    display.fill_rect(x + col * scale, y + row * scale, scale, scale, 1)
        x += 7 * scale


def centred(text, y):
    display.text(text, (128 - 8 * len(text)) // 2, y, 1)


def dotted_line(x0, y0, x1, y1, step=3):
    steps = max(abs(x1 - x0), abs(y1 - y0)) // step or 1
    for i in range(steps + 1):
        display.pixel(x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps, 1)


def arrow(x, y, up, lit):
    if not lit:
        return
    display.vline(x + 2, y, 8, 1)
    tip = y if up else y + 7
    side = tip + 2 if up else tip - 2
    display.line(x, side, x + 2, tip, 1)
    display.line(x + 4, side, x + 2, tip, 1)


def signal_bars(x, y, dbm):
    level = 0 if dbm is None else sum(dbm > edge for edge in (-115, -100, -85, -70))
    for i in range(4):
        height = 2 + 2 * i
        if i < level:
            display.fill_rect(x + 3 * i, y + 8 - height, 2, height, 1)
        else:
            display.pixel(x + 3 * i, y + 7, 1)


def sd_icon(x, y):
    display.fill_rect(x, y, 7, 9, 1)
    display.fill_rect(x + 5, y, 2, 2, 0)  # the clipped corner
    for i in range(3):
        display.vline(x + 1 + 2 * i, y + 1, 2, 0)


def battery_icon(x, y, fraction):
    display.rect(x, y + 1, 13, 7, 1)
    display.vline(x + 13, y + 3, 3, 1)
    display.fill_rect(x + 2, y + 3, round(9 * fraction), 3, 1)


def top_bar(now):
    display.text("%04X" % me, 0, 1, 1)
    arrow(38, 1, True, ticks_diff(now, sent_at) < 400)
    arrow(45, 1, False, heard_at is not None and ticks_diff(now, heard_at) < 400)
    signal_bars(60, 1, rssi if linked(now) else None)
    if sd_mounted:
        sd_icon(92, 0)
    battery_icon(112, 1, battery_level)
    display.hline(0, 11, 128, 1)


def graph(y_top, y_bottom):
    """The signal strength of recent beacons, newest on the right, two pixels each."""
    span = y_bottom - y_top
    points = [(128 - 2 * (len(history) - i), y_bottom - (min(max(dbm, -130), -40) + 130) * span // 90)
              for i, dbm in enumerate(history)]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        display.line(x0, y0, x1, y1, 1)
    for x, y in points:
        # A dithered fill under the line: every other pixel, which reads as grey on the OLED.
        for fill_y in range(y + 2, y_bottom + 1, 2):
            display.pixel(x + (fill_y // 2) % 2, fill_y, 1)
    display.hline(0, y_bottom + 1, 128, 1)


def link_screen(now):
    text = "%d" % rssi
    big(text, 0, 14, 3)
    display.text("dBm", 92, 15, 1)
    display.text("%+.1f" % snr, 90, 27, 1)
    graph(40, 53)
    # The bottom line cycles through the rest, a couple of seconds each.
    pages = ["PEER %04X #%d" % (peer, peer_seq),
             "THEY HEAR " + ("%d" % they_hear if they_hear is not None else "--"),
             "LOSS %d%%  RX %d" % (100 * missed // max(1, received + missed), received),
             "LOG %d ROWS" % logged if sd_mounted else "NO SD CARD"]
    centred(pages[now // 2500 % len(pages)], 56)


def search_screen(now):
    cx, cy, r = 64, 36, 19
    display.ellipse(cx, cy, r, r, 1)
    dotted_line(cx - r, cy, cx + r, cy)
    dotted_line(cx, cy - r, cx, cy + r)
    for i in range(0, 360, 30):
        display.pixel(cx + round(10 * cos(i / 57.3)), cy + round(10 * sin(i / 57.3)), 1)
    # The sweep, with a dotted trail behind it.
    angle = now / 500
    for lag in (0.5, 0.25):
        dotted_line(cx, cy, cx + round(r * cos(angle - lag)), cy + round(r * sin(angle - lag)))
    display.line(cx, cy, cx + round(r * cos(angle)), cy + round(r * sin(angle)), 1)

    display.text("TX", 0, 22, 1)
    display.text("%d" % seq, 0, 32, 1)
    display.text("SF%d" % spreading_factor, 96, 22, 1)
    display.text("%d" % (frequency // 1_000_000), 96, 32, 1)
    if heard_at is None:
        centred("SEARCHING" + "." * (now // 400 % 4), 56)
    else:
        centred("LOST %ds" % (ticks_diff(now, heard_at) // 1000), 56)


def splash():
    """Radio waves rising from an antenna, then the title slides up into place."""
    for frame in range(30):
        display.fill(0)
        display.vline(64, 14, 22, 1)
        display.line(58, 35, 64, 25, 1)
        display.line(70, 35, 64, 25, 1)
        display.fill_rect(62, 12, 5, 3, 1)
        for i in range(3):
            radius = (frame * 2 + i * 10) % 30
            if radius > 4:
                display.ellipse(64, 13, radius, radius, 1, False, 0b0011)  # the upper half only
        if frame > 12:
            y = max(40, 64 - (frame - 12) * 3)
            centred("LORA LINK", y)
            centred("%04X  %dMHz" % (me, frequency // 1_000_000), y + 12)
        display.show()
        sleep_ms(40)
    sleep_ms(600)


# --- SD card: optional, and picked up whenever one is pushed in --------------------------------
def try_sd():
    global sd_mounted
    if sd is None:
        return
    try:
        os.mount(sd, "/sd")
    except OSError:
        return  # no card, or not one that can be read: try again in a while
    sd_mounted = True
    if LOG[4:] not in os.listdir("/sd"):
        with open(LOG, "w") as f:
            f.write("uptime_s,peer,seq,rssi_dbm,snr_db,they_hear_dbm,missed\n")
    print("SD card found: logging to", LOG)


def log(line):
    global sd_mounted, logged
    try:
        with open(LOG, "a") as f:
            f.write(line)
        logged += 1
    except OSError:
        # The card was pulled out. Forget it until one is pushed back in.
        sd_mounted = False
        try:
            os.umount("/sd")
        except OSError:
            pass
        print("SD card gone")


# --- The link ------------------------------------------------------------------------------------
peer = None  # the other board's ID, once heard
peer_seq = 0
seq = 0
rssi = snr = they_hear = None
history = []
received = missed = logged = 0
expected = None
heard_at = None
sent_at = ticks_add(ticks_ms(), -10_000)
sd_mounted = False
battery_level = 0.0


def linked(now):
    return heard_at is not None and ticks_diff(now, heard_at) < lost_after_ms


def byte(value):
    return min(max(round(value), -127), 127)


def beacon():
    """Eight bytes: who this is, a counter, and how well this board hears the other one."""
    heard = byte(rssi) if rssi is not None else -128
    quality = byte(snr * 4) if snr is not None else 0
    return pack(">2sHHbb", MAGIC, me, seq & 0xFFFF, heard, quality)


def heard(packet, now):
    global peer, peer_seq, rssi, snr, they_hear, received, missed, expected, heard_at, history
    if len(packet) != 8 or packet[:2] != MAGIC:
        return  # somebody else's LoRa on the same settings
    _, sender, peer_seq, their_rssi, _ = unpack(">2sHHbb", packet)
    if sender != peer:
        peer, expected, received, missed, history = sender, None, 0, 0, []

    # A gap in the other board's counter means beacons were lost. A huge one means it restarted.
    if expected is not None:
        gap = (peer_seq - expected) & 0xFFFF
        if gap < 1000:
            missed += gap
    expected = (peer_seq + 1) & 0xFFFF
    received += 1

    rssi, snr = round(lora.rssi), lora.snr
    they_hear = None if their_rssi == -128 else their_rssi
    history = history[-63:] + [rssi]
    heard_at = now
    led(1)

    print("RSSI: %d  SNR: %.1f  They hear: %s  Missed: %d" %
          (rssi, snr, they_hear if they_hear is not None else "-", missed))
    if sd_mounted:
        log("%d,%04X,%d,%d,%.1f,%s,%d\n" % (now // 1000, peer, peer_seq, rssi, snr,
                                             they_hear if they_hear is not None else "", missed))


def read_battery():
    global battery_level
    volts = battery.read_uv() * battery_scale / 1_000_000
    battery_level = min(max((volts - 3.3) / 0.9, 0), 1)  # 3.3V empty, 4.2V full


print("LoRa link %04X on %.1f MHz" % (me, frequency / 1e6))
splash()
read_battery()
try_sd()
lora.receive()

now = ticks_ms()
next_beacon = ticks_add(now, urandom(1)[0] * 4)  # boards switched on together still spread out
next_sd = ticks_add(now, 10_000)
next_battery = ticks_add(now, 5000)

while True:
    now = ticks_ms()

    packet = lora.recv()
    if packet:
        heard(packet, now)

    if ticks_diff(now, next_beacon) >= 0:
        seq += 1
        lora.send(beacon())  # listening resumes straight after
        sent_at = now
        next_beacon = ticks_add(now, interval_ms - 1000 + urandom(1)[0] * 8)

    if heard_at is None or ticks_diff(now, heard_at) > 80:
        led(0)  # a short blink for each beacon heard
    if not sd_mounted and ticks_diff(now, next_sd) >= 0:
        try_sd()
        next_sd = ticks_add(now, 10_000)
    if ticks_diff(now, next_battery) >= 0:
        read_battery()
        next_battery = ticks_add(now, 5000)

    display.fill(0)
    top_bar(now)
    if linked(now):
        link_screen(now)
    else:
        search_screen(now)
    display.show()
