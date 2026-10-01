# Run with: python3 -B drivers/hx711/test_hx711.py
# A fake HX711 behind two fake pins: it shifts readings out on the clock and counts the extra
# pulses, to check the bit order, sign, gain selection and weight maths off-board.
import sys, time, types


class _Chip:
    def __init__(self, readings=(), connected=True):
        self.readings = list(readings)
        self.connected = connected
        self.pulses = 0
        self.word = None
        self.gains = []  # extra pulses after each reading, i.e. the gain asked for next
        self.powered = True

    def dout(self):
        if not self.connected:
            return 1  # never ready
        if self.pulses == 0:
            return 0  # a reading is waiting
        if self.pulses > 24:  # the driver is waiting for the next reading: finish this one
            self.gains.append(self.pulses - 24)
            self.pulses = 0
            return 0
        return (self.word >> (24 - self.pulses)) & 1

    def clock(self, value):
        if value:
            if self.pulses == 0:
                self.word = (self.readings.pop(0) if self.readings else 0) & 0xFFFFFF
            self.pulses += 1


class _Pin:
    IN, OUT = 0, 1
    chip = None

    def __init__(self, number, mode):
        self.mode = mode

    def value(self, value=None):
        if self.mode == _Pin.IN:
            return _Pin.chip.dout()
        _Pin.chip.clock(value)


sys.modules["machine"] = types.SimpleNamespace(
    Pin=_Pin, disable_irq=lambda: 0, enable_irq=lambda state: None
)
time.ticks_ms = lambda: int(time.monotonic() * 1000)
time.ticks_diff = lambda a, b: a - b
time.sleep_us = lambda us: None
from hx711 import HX711  # noqa: E402


def make(readings=(), **kwargs):
    _Pin.chip = _Chip(readings)
    return HX711(5, 4, **kwargs)


# The constructor reads once to apply the gain: 1 extra pulse for 128, 3 for 64, 2 for 32.
# The fake logs a reading's pulses when the next one is polled.
for gain, pulses in ((128, 1), (64, 3), (32, 2)):
    sensor = make(gain=gain)
    sensor.read_raw()
    assert _Pin.chip.gains == [pulses], (gain, _Pin.chip.gains)

# Bits come out most significant first, in two's complement.
sensor = make([0, 0x123456, 0x7FFFFF, 0x800000, 0xFFFFFF])
assert [sensor.read_raw() for _ in range(4)] == [0x123456, 8388607, -8388608, -1]

# Changing the gain takes effect from the reading after the one that sets it.
sensor = make()
sensor.gain = 32
sensor.read_raw()
assert _Pin.chip.gains == [1, 2], _Pin.chip.gains

# The average drops the outer quarters, so one glitch does not move it.
sensor = make([0, 100, 102, 98, 100, 100, 100, 5000000, 100])
assert sensor.read(8) == 100

# Tare, calibrate with 500g, then 250g reads as 250.
sensor = make([0] + [1000] * 15 + [51000] * 15 + [26000] * 5)
assert sensor.tare() == 1000
assert sensor.calibrate(500) == 100
assert sensor.weight() == 250

# A load cell wired the other way round gives a negative scale and still weighs positive.
sensor = make([0] * 16 + [-50000] * 15 + [-25000] * 5)
sensor.tare()
sensor.calibrate(500)
assert sensor.weight() == 250

# Offset and scale passed back in skip the calibration.
sensor = make([0, 26000], offset=1000, scale=100)
assert sensor.weight(1) == 250

# Nothing connected is reported, not waited on for ever.
_Pin.chip = _Chip(connected=False)
try:
    HX711(5, 4, timeout_ms=10)
    raise AssertionError("a missing HX711 must be reported")
except OSError as error:
    assert "HX711" in str(error), error

for bad in ({"gain": 100}, {"known_weight": 0}):
    try:
        if "gain" in bad:
            make(**bad)
        else:
            make().calibrate(**bad)
        raise AssertionError("a bad setting must be refused: %r" % bad)
    except ValueError:
        pass

print("hx711: ok")
