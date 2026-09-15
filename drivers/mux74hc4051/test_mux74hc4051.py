# Run with: python3 -B drivers/mux74hc4051/test_mux74hc4051.py
# Fake pins and an ADC that reads whichever channel the select pins point at, so the bit order,
# the break before make and the settling can be checked off-board.
import sys, types

events = []


def _sleep_ms(ms):
    events.append(("sleep", ms))


sys.modules["time"] = types.SimpleNamespace(sleep_ms=_sleep_ms)
from mux74hc4051 import Mux74HC4051  # noqa: E402


class _Pin:
    OUT = 1

    def __init__(self, name):
        self.name = name
        self.level = None

    def init(self, mode, value=None):
        self.level = value
        events.append((self.name, "init", mode, value))

    def value(self, level):
        self.level = level
        events.append((self.name, level))


class _ADC:
    """Reads channel * 1000, but only while the chip is enabled."""

    def __init__(self, s0, s1, s2, enable=None):
        self.select = (s0, s1, s2)
        self.enable = enable

    def read_u16(self):
        if self.enable is not None and self.enable.level:
            return 0  # disabled: Z is disconnected
        return sum(pin.level << bit for bit, pin in enumerate(self.select)) * 1000


def mux(enable=True, **kwargs):
    pins = [_Pin("S0"), _Pin("S1"), _Pin("S2")]
    e = _Pin("E") if enable else None
    events.clear()
    device = Mux74HC4051(*pins, enable=e, adc=_ADC(*pins, enable=e), **kwargs)
    return device, pins, e


# Every pin starts as a low output: channel 0, and switched on.
device, (s0, s1, s2), e = mux()
assert events == [
    ("S0", "init", 1, 0), ("S1", "init", 1, 0), ("S2", "init", 1, 0), ("E", "init", 1, 0)
], events
assert device.channel == 0 and device.enabled

# S0 is the lowest bit: channel 5 is S0 high, S1 low, S2 high.
device.channel = 5
assert (s0.level, s1.level, s2.level) == (1, 0, 1)

# Break before make: E goes high before any select pin changes, and low only after the last.
events.clear()
device.channel = 2
assert events == [("E", 1), ("S0", 0), ("S1", 1), ("S2", 0), ("E", 0)], events

# Every channel reads back as itself, so all eight bit patterns are right.
assert device.read_all() == [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000], device.read_all()

# Switching waits settle_ms before reading; reading the same channel again does not.
device, _, e = mux(settle_ms=3)
events.clear()
device.read(4)
device.read(4)
assert [event for event in events if event[0] == "sleep"] == [("sleep", 3)], events

# Disabled, changing channel does not switch it back on.
device.enabled = False
events.clear()
device.channel = 1
assert ("E", 0) not in events and e.level == 1, events
assert device.read(1) == 0, "disconnected"
device.enabled = True
assert device.read(1) == 1000

# Without an enable pin, switching just sets the select pins.
plain, _, _ = mux(enable=False)
events.clear()
plain.channel = 7
assert events == [("S0", 1), ("S1", 1), ("S2", 1)], events
try:
    plain.enabled = False
    raise AssertionError("enabled needs an enable pin")
except ValueError:
    pass

for bad in (-1, 8, 2.5, "3"):
    try:
        device.channel = bad
        raise AssertionError("an impossible channel must be refused: %r" % (bad,))
    except ValueError:
        pass
assert device.channel == 1, "and the channel is left as it was"

bare = Mux74HC4051(_Pin("S0"), _Pin("S1"), _Pin("S2"))
try:
    bare.read(0)
    raise AssertionError("read needs an adc")
except ValueError:
    pass

print("mux74hc4051: ok")
