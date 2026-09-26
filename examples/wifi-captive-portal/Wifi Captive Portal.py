# A captive portal: the page that opens by itself when a phone joins a network, the way a hotel
# wifi or a smart plug being set up does it.
#
# Two small servers share one loop. A DNS server answers every name with the board's own
# address, and a web server answers every page with a form. A phone checking "do I have
# internet?" gets the form instead of the reply it expected, and opens it for you.

import select
import socket
import wifi

# --- Configuration ---------------------------------------------------------------------------
# the name that will appear in the wifi list on a phone
ssid = "pulsar-setup"
# None for an open network. Portals are nearly always open: a phone joins without asking
# anything, and the portal is where the asking happens.
password = None
# the board's own address. Not the usual 192.168.4.1: Android, Samsung phones especially, never
# even sends its internet check when the name resolves to a private address, so the pop-up never
# comes. An address that looks public fixes that, and with no internet behind the board it
# cannot clash with the real owner of it.
address = "4.3.2.1"
# ----------------------------------------------------------------------------------------------

ap = wifi.access_point(ssid, password)

# Move the board to that address, and hand it out as the DNS server to everyone who joins. An
# ESP32 hands out 0.0.0.0 unless told, and then a phone's lookups never reach the server below.
ap.ifconfig((address, "255.255.255.0", address, address))

print("Network:", ssid)
print("Join it with a phone; the setup page should open by itself")

PAGE = b"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Connection: close\r
\r
<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Setup</title></head>
<body style="font-family: sans-serif; max-width: 20rem; margin: 3rem auto; padding: 0 1rem">
<h1>Set up this board</h1>
<form action="/save">
<p><label>Wifi network<br><input name="ssid" autocapitalize="none"></label></p>
<p><label>Password<br><input name="password" type="password"></label></p>
<p><button>Save</button></p>
</form>
</body></html>
"""

SAVED = b"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Connection: close\r
\r
<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Saved</title></head>
<body style="font-family: sans-serif; max-width: 20rem; margin: 3rem auto; padding: 0 1rem">
<h1>Saved</h1><p>You can close this page.</p>
</body></html>
"""

# Sends the browser to the board's own address, whatever it asked for.
REDIRECT = ("HTTP/1.1 302 Found\r\nLocation: http://%s/\r\nContent-Length: 0\r\n"
            "Connection: close\r\n\r\n" % address).encode()


def dns_reply(query, address):
    """Answers a DNS query: whatever name was asked for, it is at this board's address."""
    # The question follows the 12-byte header: the name as length-prefixed labels ending in a
    # zero byte, then two bytes of type and two of class.
    end = 12
    while query[end]:
        end += query[end] + 1
    end += 5
    question = query[12:end]
    # Keep the query's id, set "this is a response", one question.
    header = query[:2] + b"\x81\x80\x00\x01"
    # Only an A record (type 1, an IPv4 address) gets an answer. Anything else, such as the
    # AAAA a phone asks for alongside it, gets an empty one, so the phone settles for IPv4.
    if question[-4:-2] != b"\x00\x01":
        return header + b"\x00\x00\x00\x00\x00\x00" + question
    # The answer points back at the name in the question (0xc00c), and lasts 60 seconds.
    return (header + b"\x00\x01\x00\x00\x00\x00" + question
            + b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
            + bytes(int(part) for part in address.split(".")))


def unquote(text):
    """Undoes what a browser does to a form field: + for a space, %xx for anything unusual."""
    parts = text.replace(b"+", b" ").split(b"%")
    decoded = parts[0]
    for part in parts[1:]:
        decoded += bytes([int(part[:2], 16)]) + part[2:]
    return decoded.decode()


def serve(connection):
    lines = connection.recv(1024).split(b"\r\n")
    path = lines[0].split(b" ")[1]
    host = b""
    for line in lines[1:]:
        if line.lower().startswith(b"host:"):
            host = line[5:].strip()

    # A phone checking for internet asks for a page on someone else's server. The DNS server
    # sent it here, and a redirect instead of the reply it wanted is what makes it open the
    # portal. Asking for the board by address gets the real page.
    if host != address.encode():
        connection.send(REDIRECT)
    elif path.startswith(b"/save?"):
        # ponytail: the form is sent as GET, so the password is in the URL. It never leaves the
        # phone and the board, but a POST is the thing to switch to if that matters.
        fields = {}
        for pair in path[6:].split(b"&"):
            key, _, value = pair.partition(b"=")
            fields[key] = unquote(value)
        connection.send(SAVED)
        # Printing the password itself to a serial port is a habit worth not getting into.
        print("Received network %r, password of %d characters"
              % (fields.get(b"ssid", ""), len(fields.get(b"password", ""))))
    else:
        connection.send(PAGE)


# Port 53 is DNS, and it is UDP: one packet in, one packet out, no connection.
dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dns.bind(socket.getaddrinfo("0.0.0.0", 53)[0][-1])

web = socket.socket()
web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
web.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])
# A phone fires several checks at once when it joins, so let a few of them wait their turn.
web.listen(5)

# poll waits on both sockets at once and says which one has something, so neither server
# blocks the other.
poller = select.poll()
poller.register(dns, select.POLLIN)
poller.register(web, select.POLLIN)

while True:
    for ready in poller.poll():
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
