# Run with: python3 -B drivers/wifi/test_wifi.py
# Two fake `network` modules, numbered the way an ESP32 and a Pico W really number their status
# codes, because a driver that only works on the board it was written on is the thing this is
# meant to prevent.
import sys, types

clock = [0]
sys.modules["time"] = types.SimpleNamespace(
    ticks_ms=lambda: clock[0],
    ticks_add=lambda ticks, delta: ticks + delta,
    ticks_diff=lambda a, b: a - b,
    sleep_ms=lambda ms: clock.__setitem__(0, clock[0] + ms),
)

# The real numbers, from ports/esp32 and ports/rp2. They share not one value.
ESP32 = dict(STAT_IDLE=1000, STAT_CONNECTING=1001, STAT_GOT_IP=1010, STAT_NO_AP_FOUND=201,
             STAT_WRONG_PASSWORD=202, STAT_BEACON_TIMEOUT=200, STAT_ASSOC_FAIL=203,
             STAT_HANDSHAKE_TIMEOUT=204, AUTH_WPA_WPA2_PSK=4)
PICO_W = dict(STAT_IDLE=0, STAT_CONNECTING=1, STAT_GOT_IP=3, STAT_NO_AP_FOUND=-2,
              STAT_WRONG_PASSWORD=-3, STAT_CONNECT_FAIL=-1)


class _WLAN:
    PM_NONE = 0xA11140

    def __init__(self, interface):
        self.interface = interface
        self.is_active = False
        self.connected = False
        self.state = None
        self.config_calls = []
        self.order = []
        self.script = []

    def active(self, value=None):
        if value is None:
            return self.is_active
        self.is_active = value
        self.order.append("active")

    def config(self, **kwargs):
        if "authmode" in kwargs and "authmode" not in self.accepts:
            raise ValueError("unknown config param")
        if "pm" in kwargs and "pm" not in self.accepts:
            raise ValueError("unknown config param")
        self.config_calls.append(kwargs)
        self.order.append("config")

    def connect(self, ssid, password=None):
        self.attempt = (ssid, password)

    def disconnect(self):
        self.connected = False

    def isconnected(self):
        if self.script:
            self.state = self.script.pop(0)
        return self.state == "connected"

    def status(self):
        return self.statuses[self.state]

    def ifconfig(self):
        return ("192.168.1.50", "255.255.255.0", "192.168.1.1", "192.168.1.1")


# One fake module, whose contents are swapped for each board. Replacing sys.modules["network"]
# instead would not work: the driver imported the old object and still holds it.
network = types.SimpleNamespace(STA_IF="sta", AP_IF="ap")
sys.modules["network"] = network
import wifi  # noqa: E402


def board(constants, accepts=("authmode", "pm")):
    """Turns the fake `network` into one kind of board, and hands back its interfaces."""
    for name in [key for key in vars(network) if key.startswith(("STAT_", "AUTH_"))]:
        delattr(network, name)
    for name, value in constants.items():
        setattr(network, name, value)

    interfaces = {}

    def wlan(interface):
        if interface not in interfaces:
            made = _WLAN(interface)
            made.accepts = accepts
            made.statuses = {
                None: constants["STAT_IDLE"],
                "connecting": constants["STAT_CONNECTING"],
                "connected": constants["STAT_GOT_IP"],
                "wrong password": constants["STAT_WRONG_PASSWORD"],
                "missing": constants["STAT_NO_AP_FOUND"],
            }
            interfaces[interface] = made
        return interfaces[interface]

    network.WLAN = wlan
    return interfaces, wlan


for constants, label in ((ESP32, "esp32"), (PICO_W, "pico w")):
    interfaces, wlan = board(constants)

    # The names come out of the firmware, so both boards read the same however they are numbered.
    assert wifi.describe(constants["STAT_GOT_IP"]) == "got ip", label
    assert wifi.describe(constants["STAT_WRONG_PASSWORD"]) == "wrong password", label
    assert wifi.describe(999999) == "status 999999", "an unknown code is still readable"

    # A connection that takes a few tries before it comes up.
    station = wlan("sta")
    station.script = ["connecting", "connecting", "connected"]
    clock[0] = 0
    assert wifi.connect("home", "secret", timeout=10) is station, label
    assert station.attempt == ("home", "secret")
    assert wifi.address(station) == "192.168.1.50"
    assert wifi.details(station)["dns"] == "192.168.1.1"

    # A wrong password is reported straight away, in words, rather than waiting out the timeout.
    interfaces, wlan = board(constants)
    station = wlan("sta")
    station.script = ["wrong password"] * 5
    clock[0] = 0
    try:
        wifi.connect("home", "wrong", timeout=10)
        raise AssertionError("a wrong password must be reported")
    except OSError as error:
        assert "wrong password" in str(error), (label, error)
    assert clock[0] < 1000, "and without waiting the whole timeout out"

    # A network that never answers gives up when it said it would, and says what it last saw.
    station.script = ["connecting"] * 500
    clock[0] = 0
    try:
        wifi.connect("home", "secret", timeout=2)
        raise AssertionError("it must give up")
    except OSError as error:
        assert "Timed out" in str(error) and "connecting" in str(error), error
    assert clock[0] >= 2000, label

# An access point is configured both before and after being switched on, because the two ports
# document opposite orders and doing both satisfies either.
interfaces, wlan = board(ESP32)
ap = wifi.access_point("pulsar", "hunter2hunter")
assert ap.order[:3] == ["config", "active", "config"], ap.order
assert ap.config_calls[0] == {"essid": "pulsar", "password": "hunter2hunter"}
assert {"authmode": ESP32["AUTH_WPA_WPA2_PSK"]} in ap.config_calls, "the esp32 is told to use WPA2"
assert ap.is_active

# A board that rejects authmode, as the Pico W does, still comes up.
interfaces, wlan = board(PICO_W, accepts=())
ap = wifi.access_point("pulsar", "hunter2hunter")
assert ap.is_active, "refusing the setting is not a failure"
assert all("authmode" not in call for call in ap.config_calls)

# A password too short is refused here rather than by the firmware, where the error is obscure.
try:
    wifi.access_point("pulsar", "short")
    raise AssertionError("a short password must be refused")
except ValueError as error:
    assert "8 characters" in str(error)

# An open access point needs no password and is not given one.
interfaces, wlan = board(PICO_W, accepts=())  # a fresh board, so the calls below are its own
ap = wifi.access_point("open-network")
assert ap.config_calls[0] == {"essid": "open-network"}

print("wifi: ok")
