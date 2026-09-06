# Run with: python3 -B drivers/ir-transmitter/test_ir_transmitter.py
# Checks the frames this driver builds by decoding them with the receiver driver, which is the
# real question: would the thing on the other end understand them?
import os, sys, types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ir-receiver"))
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["machine"] = types.SimpleNamespace(Pin=object, Timer=object, PWM=None)
sys.modules["time"] = types.SimpleNamespace(
    ticks_us=lambda: 0, ticks_diff=lambda a, b: a - b, sleep_us=lambda us: None,
    sleep_ms=lambda ms: None,
)
from ir_receiver import REPEAT, decode  # noqa: E402
from ir_transmitter import IRTransmitter, encode  # noqa: E402


class _Carrier:
    """Stands in for the hardware, keeping what it was asked to send."""

    name = "test"

    def __init__(self):
        self.frames = []

    def send(self, pulses):
        self.frames.append(list(pulses))


# What this driver builds, the receiver driver reads back. If either end drifts, this fails.
for address, command in ((0x00, 0x45), (0xEF, 0x16), (0xFF, 0x00), (0x2A3C, 0x07)):
    assert decode(encode(address, command)) == (address, command), (address, command)

# The frame is the right shape: a leader, 32 bits of mark and space, and a stop mark.
pulses = encode(0x00, 0x45)
assert len(pulses) == 2 + 64 + 1, len(pulses)
assert pulses[0] == 9000 and pulses[1] == 4500
assert all(pulses[2 + bit * 2] == 560 for bit in range(32)), "every bit starts with a mark"
assert set(pulses[3 :: 2][:32]) <= {560, 1690}, "spaces are only long or short"

# An address that fits in a byte is sent the plain way, twice, the second time inverted.
plain = encode(0x04, 0x08)
value = sum(1 << bit for bit in range(32) if plain[3 + bit * 2] == 1690)
assert value & 0xFF == 0x04 and (value >> 8) & 0xFF == 0xFB, hex(value)

# A repeat is the shorter frame, and the receiver reads it as one.
transmitter = IRTransmitter(None, carrier=_Carrier())
transmitter.send(0x00, 0x45, repeats=2)
sent = transmitter._carrier.frames
assert len(sent) == 3, "one press and two repeats"
assert decode(sent[0]) == (0x00, 0x45)
assert decode(sent[1]) == REPEAT and decode(sent[2]) == REPEAT

# Raw pulses go straight out, for a protocol this driver does not know.
transmitter.send_raw((1000, 500, 1000))
assert transmitter._carrier.frames[-1] == [1000, 500, 1000]

# The backend is chosen by what the board has, not by asking it what it is.
class _FakeRMT:
    def __init__(self, channel, pin=None, clock_div=None, tx_carrier=None):
        self.tx_carrier = tx_carrier
        self.sent = None

    def write_pulses(self, pulses, start):
        self.sent = (pulses, start)

    def wait_done(self, timeout=0):
        return True


sys.modules["esp32"] = types.SimpleNamespace(RMT=_FakeRMT)
transmitter = IRTransmitter(None)
assert transmitter.backend == "rmt", "the hardware peripheral is preferred"
transmitter.send(0x00, 0x45)
sent, start = transmitter._carrier._rmt.sent
assert start == 1, "the train starts with the carrier on"
assert decode(list(sent)) == (0x00, 0x45)
assert transmitter._carrier._rmt.tx_carrier == (38000, 33, 1)

del sys.modules["esp32"]


class _FakePWM:
    def __init__(self, pin):
        self.duties = []

    def freq(self, value):
        self.frequency = value

    def duty_u16(self, value):
        self.duties.append(value)


sys.modules["machine"] = types.SimpleNamespace(Pin=object, Timer=object, PWM=_FakePWM)
transmitter = IRTransmitter(None)
assert transmitter.backend == "pwm", "without RMT it falls back rather than failing"
transmitter.send(0x00, 0x45)
duties = transmitter._carrier._pwm.duties
assert transmitter._carrier._pwm.frequency == 38000
assert duties[1] > 0 and duties[2] == 0, "marks run the carrier, spaces are silent"
assert duties[-1] == 0, "and the LED is left off"

print("ir_transmitter: ok")
