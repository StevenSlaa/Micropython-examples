# A message board on the 640x180 touch screen. The board makes its own wifi network, and whatever
# is sent to it appears on screen straight away. Two ways in: a phone joins the network and a page
# opens by itself with a form, or another board sends a message over ESP-NOW. Hand it to a class and
# see who gets the first message up.
#
# Three things share one loop. The screen redraws only the rows that changed, a DNS server answers
# every name with the board's own address so the page pops up on its own, and a web server answers
# every page with the form. ESP-NOW listens on the same radio the access point uses.

import espnow
import network
import select
import socket
from machine import I2C, Pin
from time import ticks_add, ticks_diff, ticks_ms
from axs15231b import AXS15231B, AXS15231BTouch, color565, WHITE
from sy6970 import SY6970
import pulsar_ui
import wifi

# Configuration
# the name that appears in the wifi list on a phone
ssid = "pulsar-board"
# None for an open network. A portal is nearly always open: a phone joins without being asked
# anything, and the page is where the asking happens.
password = None
# 1 to 13. A board sending over ESP-NOW must be on this channel too.
channel = 1
# the board's own address. Not the usual 192.168.4.1: Android, Samsung phones especially, never even
# sends its internet check when the name resolves to a private address, so the pop-up never comes.
# An address that looks public fixes that, and with no internet behind the board it cannot clash.
address = "4.3.2.1"
# how long one frame lasts. What is left of it goes to the network, not to a sleep, so a phone never
# waits more than this for its page.
frame_ms = 30
# the longest message kept. 72 characters of 8x8 text is what fits a row next to its tag.
message_length = 72
# 1 or 3 is landscape, which the layout needs: 1 has the USB port on the right, 3 on the left
rotation = 1
# set this to True if a LiPo battery is plugged into the board
battery = False

# The board's battery charger, an SY6970, shares this I2C bus with the touch. Its driver switches off
# the chip's watchdog, which otherwise resets its settings every 40 seconds. The chip also keeps
# trying to charge when no battery is connected, which froze the tested board after a few minutes,
# so charging is only on with a battery.
i2c = I2C(0, scl=Pin(10), sda=Pin(15), freq=400000)
charger = SY6970(i2c)
charger.charge_enabled = battery

display = AXS15231B(rotation=rotation)
touch = AXS15231BTouch(i2c, rotation=rotation)

ap = wifi.access_point(ssid, password, channel=channel)
# Move the board to that address, and hand it out as the DNS server to everyone who joins. An ESP32
# hands out 0.0.0.0 unless told, and then a phone's lookups never reach the server below.
ap.ifconfig((address, "255.255.255.0", address, address))

# ESP-NOW rides on the same radio as the access point, so it listens on the channel above. The
# station interface is switched on because ESP-NOW wants one; it never connects anywhere.
network.WLAN(network.STA_IF).active(True)
esp = espnow.ESPNow()
esp.active(True)

ap_mac = ap.config("mac")
print("Network:", ssid, "on channel", channel)
print("Join it with a phone; the message page should open by itself")
print('Sender setting: receiver = b"' + "".join("\\x%02x" % b for b in ap_mac) + '"')
print("Sender setting: channel =", channel)

# Colours
BACKGROUND = color565(12, 16, 28)
PANEL = color565(30, 36, 56)
MUTED = color565(140, 150, 175)
BRAND = color565(240, 64, 64)  # the red of "IoT" in the logo
WATER = color565(80, 160, 255)
GOOD = color565(60, 200, 110)

# Layout of the 640x180 screen: a header, seven rows of a tag and a message, and a footer
ROWS, ROW_TOP, ROW_HEIGHT = 7, 38, 17
TAG_X, TEXT_X = 8, 48
COUNT_X = 452
CLEAR_X, CLEAR_Y, CLEAR_WIDTH, CLEAR_HEIGHT = 566, 5, 68, 17
FOOTER_Y = 164

# What is on each row right now, so only changes are redrawn
EMPTY = ("", "", MUTED)
HINT = ("", "NOTHING YET. JOIN THE NETWORK, OR SEND OVER ESP-NOW.", MUTED)
shown = [EMPTY] * ROWS  # the background is already clear, so an empty row needs no drawing
shown_count = None

messages = []  # newest first, at most ROWS of (tag, text, tag colour)
total = 0


def draw_once():
    """Everything that never changes: the background, the logo, the hint and the clear button."""
    display.fill(BACKGROUND)
    for x, y, width, height, colour, bitmap in pulsar_ui.LOGO:
        display.bitmap(bitmap, x, y, width, height, BRAND if colour == "RED" else WHITE, BACKGROUND)
    # the 1 bit swirl was made for e-paper; on this sharp screen the smooth colour icon replaces it
    display.blit_buffer(pulsar_ui.ICON, 4, 1, pulsar_ui.ICON_SIZE, pulsar_ui.ICON_SIZE)
    display.text('JOIN "%s" TO POST' % ssid.upper(), 236, 11, MUTED, BACKGROUND)
    display.fill_rect(CLEAR_X, CLEAR_Y, CLEAR_WIDTH, CLEAR_HEIGHT, PANEL)
    display.text("CLEAR", CLEAR_X + 14, 10, BRAND, PANEL)
    display.hline(0, 29, display.width, PANEL)
    # everything a sending board needs is on the screen, so nothing has to be read from the REPL
    display.text("MY MAC %s  CH %d  http://%s" % (ap_mac.hex(":"), channel, address),
                 TAG_X, FOOTER_Y, MUTED, BACKGROUND)


def draw_rows():
    """Redraws the rows whose contents changed, straight over the old ones."""
    for index in range(ROWS):
        if messages:
            row = messages[index] if index < len(messages) else EMPTY
        else:
            row = HINT if index == 0 else EMPTY
        if row == shown[index]:
            continue
        tag, text, colour = row
        y = ROW_TOP + index * ROW_HEIGHT
        display.text("%-4s" % tag, TAG_X, y, colour, BACKGROUND)
        # padded to the full width, so a shorter message leaves none of the last one behind
        display.text(text + " " * (message_length - len(text)), TEXT_X, y,
                     WHITE if tag else MUTED, BACKGROUND)
        shown[index] = row


def draw_count():
    """The count in the header, redrawn only when it changes."""
    global shown_count
    if total != shown_count:
        display.text("RECEIVED %-4d" % total, COUNT_X, 11, MUTED, BACKGROUND)
        shown_count = total


def add(tag, text, colour):
    """Puts a message at the top of the board and drops the oldest one off the bottom."""
    global total
    # the 8x8 font is ASCII, and a message comes from a phone or the air: anything it cannot draw
    # would come out as rubbish, so it becomes a space
    text = "".join(c if " " <= c <= "~" else " " for c in text)[:message_length].strip()
    if not text:
        return
    messages.insert(0, (tag, text, colour))
    del messages[ROWS:]
    total += 1
    print("%s: %s" % (tag, text))


def clear():
    """Empties the board, back to the starting hint."""
    global total
    del messages[:]
    total = 0


def tapped(point):
    """A new touch: the clear button is the only thing on screen that reacts."""
    x, y = point
    # ponytail: a generous corner, not the pill itself; a 68x17 target is smaller than a fingertip
    if x > CLEAR_X - 16 and y < 30:
        clear()


def unquote(text):
    """Undoes what a browser does to a form field: + for a space, %xx for anything unusual."""
    parts = text.replace(b"+", b" ").split(b"%")
    decoded = parts[0]
    for part in parts[1:]:
        decoded += bytes([int(part[:2], 16)]) + part[2:]
    return decoded.decode()


def page(note=""):
    """The form, with a line above it when the last message went through."""
    # ponytail: the message is never echoed back into this page, only drawn on the screen, so
    # nothing here needs escaping.
    return ("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
            "<!doctype html><html><head>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>Message board</title></head>"
            "<body style='font-family:sans-serif;max-width:22rem;margin:3rem auto;padding:0 1rem'>"
            "<h1>Message board</h1>" + note +
            "<form action='/say'><p><input name=text autofocus autocomplete=off maxlength="
            + str(message_length) +
            " style='width:100%;padding:.6rem;font-size:1rem'></p>"
            "<p><button style='padding:.6rem 1.2rem;font-size:1rem'>Send</button></p></form>"
            "</body></html>").encode()


SENT = "<p style='color:#1f9d55'>Sent. Look at the board.</p>"

# Sends the browser to the board's own address, whatever it asked for.
REDIRECT = ("HTTP/1.1 302 Found\r\nLocation: http://%s/\r\nContent-Length: 0\r\n"
            "Connection: close\r\n\r\n" % address).encode()


def dns_reply(query, address):
    """Answers a DNS query: whatever name was asked for, it is at this board's address."""
    # The question follows the 12-byte header: the name as length-prefixed labels ending in a zero
    # byte, then two bytes of type and two of class.
    end = 12
    while query[end]:
        end += query[end] + 1
    end += 5
    question = query[12:end]
    # Keep the query's id, set "this is a response", one question.
    header = query[:2] + b"\x81\x80\x00\x01"
    # Only an A record (type 1, an IPv4 address) gets an answer. Anything else, such as the AAAA a
    # phone asks for alongside it, gets an empty one, so the phone settles for IPv4.
    if question[-4:-2] != b"\x00\x01":
        return header + b"\x00\x00\x00\x00\x00\x00" + question
    # The answer points back at the name in the question (0xc00c), and lasts 60 seconds.
    return (header + b"\x00\x01\x00\x00\x00\x00" + question
            + b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
            + bytes(int(part) for part in address.split(".")))


def serve(connection):
    """Answers one request: the form, the form with the message added, or a push to the portal."""
    lines = connection.recv(1024).split(b"\r\n")
    path = lines[0].split(b" ")[1]
    host = b""
    for line in lines[1:]:
        if line.lower().startswith(b"host:"):
            host = line[5:].strip()

    # A phone checking for internet asks for a page on someone else's server. The DNS server sent it
    # here, and a redirect instead of the reply it wanted is what makes it open the portal. Asking
    # for the board by address gets the real page.
    if host != address.encode():
        connection.send(REDIRECT)
    elif path.startswith(b"/say?"):
        for pair in path[5:].split(b"&"):
            key, _, value = pair.partition(b"=")
            if key == b"text":
                add("WEB", unquote(value), WATER)
        connection.send(page(SENT))
    else:
        connection.send(page())


# Port 53 is DNS, and it is UDP: one packet in, one packet out, no connection.
dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dns.bind(socket.getaddrinfo("0.0.0.0", 53)[0][-1])

web = socket.socket()
web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
web.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])
# A phone fires several checks at once when it joins, so let a few of them wait their turn.
web.listen(5)

# poll waits on both sockets at once and says which one has something, so neither server blocks the
# other, and waiting on it is what paces the loop.
poller = select.poll()
poller.register(dns, select.POLLIN)
poller.register(web, select.POLLIN)


def serve_until(deadline):
    """Answers the network until the frame runs out. This is the loop's sleep."""
    while True:
        remaining = ticks_diff(deadline, ticks_ms())
        if remaining <= 0:
            return
        for ready in poller.poll(remaining):
            if ready[0] is dns:
                query, caller = dns.recvfrom(512)
                try:
                    dns.sendto(dns_reply(query, address), caller)
                except (IndexError, OSError):
                    # A packet too short to be a query. Not worth stopping for.
                    pass
            else:
                connection, caller = web.accept()
                # Without a timeout, a phone that connects and never asks would stall everything.
                connection.settimeout(3)
                try:
                    serve(connection)
                except (OSError, ValueError, IndexError):
                    # A browser that gave up halfway, or a request that made no sense.
                    pass
                finally:
                    connection.close()


draw_once()
touching = None
while True:
    start = ticks_ms()

    while esp.any():
        mac, msg = esp.recv(0)
        if msg is None:
            break
        try:
            text = msg.decode()
        except UnicodeError:
            text = msg.hex()  # not text at all: show the bytes rather than nothing
        # the tag is the last two bytes of the sender's address, enough to tell boards apart
        add(mac.hex()[-4:].upper(), text, GOOD)

    draw_rows()
    draw_count()

    # only the moment a finger comes down counts as a tap, not holding it there
    point = touch.read()
    if point and not touching:
        tapped(point)
    touching = point

    serve_until(ticks_add(start, frame_ms))
