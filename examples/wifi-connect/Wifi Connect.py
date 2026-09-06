# Joining a wifi network, using the network module directly so you can see what is happening.
#
# The other networking examples use the wifi driver, which is this with the awkward parts
# handled. This one is here to show what those parts are.

import network
from time import sleep, ticks_diff, ticks_ms

# --- Configuration ---------------------------------------------------------------------------
SSID = "your-network"
PASSWORD = "your-password"
timeout = 20  # seconds to wait before giving up
# ----------------------------------------------------------------------------------------------

# STA_IF is the interface that joins somebody else's network. AP_IF, the other one, is for
# being a network yourself, which the access point example uses.
wlan = network.WLAN(network.STA_IF)

# The radio is off until this. Nothing else works before it.
wlan.active(True)

# Every port numbers its status codes differently and does not define the same ones, so
# comparing against a number from a tutorial gives a program that works on the board it was
# written on and lies on any other. Reading the names out of the firmware is the fix.
STATUS_NAMES = {
    getattr(network, name): name[5:].lower().replace("_", " ")
    for name in dir(network)
    if name.startswith("STAT_")
}

print("Joining", SSID)
wlan.connect(SSID, PASSWORD)

deadline = ticks_ms() + timeout * 1000

while not wlan.isconnected():
    status = STATUS_NAMES.get(wlan.status(), "unknown")

    # "idle" and "connecting" mean keep waiting. Anything else is a decision, and usually a
    # useful one: no ap found, wrong password.
    if status not in ("idle", "connecting"):
        print("Failed:", status)
        break

    if ticks_diff(deadline, ticks_ms()) <= 0:
        print("Timed out after", timeout, "seconds, last status:", status)
        break

    print("Status:", status)
    sleep(0.5)

if wlan.isconnected():
    # ifconfig gives four things in a fixed order, and they are easy to mix up.
    ip, netmask, gateway, dns = wlan.ifconfig()
    print("Connected")
    print("IP address:", ip)
    print("Netmask:", netmask)
    print("Gateway:", gateway)
    print("DNS server:", dns)
else:
    print("Not connected")
