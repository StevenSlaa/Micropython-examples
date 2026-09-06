# Turning names into addresses, and then actually asking one of them for something.
#
# Every connection to a name does this first. It usually happens invisibly inside whatever
# library you are using; here it is on its own, so a failure can be told apart from the
# request that follows it.

import socket
from time import sleep, ticks_diff, ticks_ms
import wifi

# --- Configuration ---------------------------------------------------------------------------
SSID = "your-network"
PASSWORD = "your-password"

# names to look up. The last one does not exist, on purpose.
NAMES = ("example.com", "micropython.org", "raspberrypi.com", "not-a-real-name.invalid")

# the page to fetch afterwards
host = "example.com"
path = "/"
# ----------------------------------------------------------------------------------------------

station = wifi.connect(SSID, PASSWORD)
network_details = wifi.details(station)

print("Connected as", network_details["ip"])
# This is who the board asks. It came from the router when the address did, and nothing in the
# program chose it.
print("Asking the DNS server at", network_details["dns"])
print()

for name in NAMES:
    started = ticks_ms()
    try:
        # getaddrinfo is the lookup. It returns a list of ways to reach the name; the address
        # itself is the last item of each, as (ip, port).
        results = socket.getaddrinfo(name, 80)
        took = ticks_diff(ticks_ms(), started)
        addresses = sorted({result[-1][0] for result in results})
        print("%-26s %-16s Lookup: %d ms" % (name, ", ".join(addresses), took))
    except OSError as error:
        took = ticks_diff(ticks_ms(), started)
        # A name that does not exist fails here, before anything is connected to.
        print("%-26s could not be resolved (%s)  Lookup: %d ms" % (name, error, took))

print()
print("Fetching http://%s%s" % (host, path))

# The same lookup again, this time to connect to.
target = socket.getaddrinfo(host, 80)[0][-1]
connection = socket.socket()
connection.settimeout(10)

try:
    connection.connect(target)
    # An HTTP request is a few lines of text. The Host header is not optional: one address
    # often serves many sites, and it is what says which one you want.
    connection.send(b"GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (path.encode(), host.encode()))

    received = 0
    first_line = b""
    while True:
        chunk = connection.recv(512)
        if not chunk:
            break
        if not first_line:
            first_line = chunk.split(b"\r\n")[0]
        received += len(chunk)

    print("Reply:", first_line.decode())
    print("Bytes: %d" % received)
finally:
    connection.close()
