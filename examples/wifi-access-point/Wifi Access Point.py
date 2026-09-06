# Being a wifi network rather than joining one, and serving a page to whoever connects.
#
# This is how a device with no screen gets configured: it puts up its own network, you join it
# with a phone, and it shows you a page.

import socket
from time import sleep
import wifi

# --- Configuration ---------------------------------------------------------------------------
# the name that will appear in the wifi list on a phone
ssid = "pulsar-setup"
# at least 8 characters, or None for a network anyone can join
password = "hunter2hunter"
# the port to serve the page on. 80 is the one browsers use without being told.
port = 80
# ----------------------------------------------------------------------------------------------

# The driver configures the interface on both sides of switching it on, because the ESP32 and
# the Pico W document opposite orders and each fails the other way round.
ap = wifi.access_point(ssid, password)
address = wifi.address(ap)

print("Network:", ssid)
print("Join it, then open http://%s%s" % (address, "" if port == 80 else ":%d" % port))

PAGE = """HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!doctype html>
<html><body style="font-family: sans-serif; text-align: center; padding-top: 3rem">
<h1>%s</h1>
<p>Served by the board itself, at %s.</p>
<p>Visitors so far: %d</p>
</body></html>
"""

# getaddrinfo turns an address and a port into something bind wants. "0.0.0.0" means listen on
# every interface this board has, which here is the access point.
listener = socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(socket.getaddrinfo("0.0.0.0", port)[0][-1])
listener.listen(1)

visitors = 0

while True:
    connection, caller = listener.accept()
    visitors += 1
    print("Visitor %d from %s" % (visitors, caller[0]))

    try:
        # Read the request and throw it away: this page is the same whatever was asked for.
        # Without reading it, some browsers never render the reply.
        connection.recv(1024)
        connection.send(PAGE % (ssid, address, visitors))
    except OSError:
        # A browser that gave up halfway is not worth stopping the whole program for.
        pass
    finally:
        connection.close()
