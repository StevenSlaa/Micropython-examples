# Listing the wifi networks around you: names, signal strength and whether they need a password.

import network
from time import sleep

# --- Configuration ---------------------------------------------------------------------------
# how often to scan again, in seconds
interval = 10
# ----------------------------------------------------------------------------------------------

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# scan() returns tuples of (ssid, bssid, channel, rssi, security, hidden). The security field
# is a number whose meaning differs between ports, so this maps only the two cases that matter.
SECURITY = {0: "open"}


def strength(rssi):
    """RSSI is in dBm and always negative. Closer to zero is stronger."""
    if rssi > -60:
        return "excellent"
    if rssi > -70:
        return "good"
    if rssi > -80:
        return "weak"
    return "barely there"


while True:
    print("Scanning...")
    networks = wlan.scan()

    # Strongest first, which is the order you care about.
    networks.sort(key=lambda entry: entry[3], reverse=True)

    print("Found: %d networks" % len(networks))
    for ssid, bssid, channel, rssi, security, hidden in networks:
        name = ssid.decode() or "(hidden)"
        locked = SECURITY.get(security, "password")
        print(
            "%-24s Channel: %2d  Signal: %4d dBm  %s, %s"
            % (name, channel, rssi, strength(rssi), locked)
        )

    print()
    sleep(interval)
