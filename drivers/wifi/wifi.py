# Connecting to wifi, and running an access point, on any board that has it: ESP32, ESP32-S3,
# Raspberry Pi Pico W and the rest.
#
# The `network` module looks the same everywhere and is not quite. Two differences bite:
#
#   Status codes  every port numbers them differently, and they do not even define the same
#                 set. Comparing against a number you copied from a tutorial gives a program
#                 that works on one board and silently misreports on another. This reads the
#                 names out of the module itself, so it is right wherever it runs.
#
#   Access points ESP32's documentation activates the interface and then configures it. The
#                 Pico W's configures it and then activates. Doing both, in that order, works
#                 on either.

import network
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

# Statuses that mean "still trying" rather than "it went wrong".
_WORKING = ("idle", "connecting")


def status_names():
    """Every STAT_ the running firmware defines, by the number it uses for it."""
    names = {}
    for name in dir(network):
        if name.startswith("STAT_"):
            names[getattr(network, name)] = name[5:].lower().replace("_", " ")
    return names


def describe(status):
    """A status code as words, or the bare number if this firmware has no name for it."""
    return status_names().get(status, "status %s" % status)


def connect(ssid, password=None, timeout=20, hostname=None, power_save=True):
    """Joins a wifi network and returns the interface, or raises OSError saying why not.

    Blocks until it has an address or `timeout` seconds have passed. `power_save=False` is
    worth setting on a Pico W that is going to answer requests: its radio sleeps between
    beacons otherwise, which shows up as replies that take hundreds of milliseconds.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if hostname:
        # Two spellings of the same idea, depending on the port and its version.
        try:
            network.hostname(hostname)
        except (AttributeError, OSError):
            try:
                wlan.config(hostname=hostname)
            except (ValueError, OSError):
                pass

    if not power_save:
        try:
            wlan.config(pm=getattr(wlan, "PM_NONE", 0xA11140))
        except (ValueError, OSError, AttributeError):
            pass  # a port that has no such setting is already not sleeping

    if wlan.isconnected():
        return wlan

    wlan.connect(ssid, password)
    deadline = ticks_add(ticks_ms(), int(timeout * 1000))
    while not wlan.isconnected():
        status = wlan.status()
        name = describe(status)
        if name not in _WORKING:
            # A definite answer, and usually a useful one: "wrong password", "no ap found".
            wlan.disconnect()
            raise OSError("Could not join %s: %s" % (ssid, name))
        if ticks_diff(deadline, ticks_ms()) <= 0:
            wlan.disconnect()
            raise OSError("Timed out joining %s after %ss (%s)" % (ssid, timeout, name))
        sleep_ms(200)
    return wlan


def access_point(ssid, password=None, channel=None, timeout=10):
    """Starts an access point other devices can join, and returns the interface.

    Without a password the network is open, which anyone nearby can join. A password must be at
    least eight characters or the firmware will refuse it.
    """
    if password is not None and len(password) < 8:
        raise ValueError("A wifi password must be at least 8 characters")

    ap = network.WLAN(network.AP_IF)
    settings = {"essid": ssid}
    if password:
        settings["password"] = password
    if channel:
        settings["channel"] = channel

    def apply():
        try:
            ap.config(**settings)
        except (ValueError, OSError):
            pass

    # The Pico W wants configuring before it is switched on and the ESP32 after, so do both.
    apply()
    ap.active(True)
    apply()

    if password:
        # The ESP32 needs to be told to use WPA2; the Pico W picks it on its own and rejects
        # being told, so this asks and moves on.
        for name in ("AUTH_WPA_WPA2_PSK", "AUTH_WPA2_PSK"):
            mode = getattr(network, name, None)
            if mode is None:
                continue
            try:
                ap.config(authmode=mode)
                break
            except (ValueError, OSError):
                pass

    deadline = ticks_add(ticks_ms(), int(timeout * 1000))
    while not ap.active():
        if ticks_diff(deadline, ticks_ms()) <= 0:
            raise OSError("The access point did not start")
        sleep_ms(100)
    return ap


def address(interface):
    """The IP address of a connected interface."""
    return interface.ifconfig()[0]


def details(interface):
    """Address, netmask, gateway and DNS server, as a dict rather than a tuple to unpack."""
    ip, netmask, gateway, dns = interface.ifconfig()
    return {"ip": ip, "netmask": netmask, "gateway": gateway, "dns": dns}


def disconnect():
    """Leaves the network and switches the radio off, which is worth doing before deep sleep."""
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(False)
