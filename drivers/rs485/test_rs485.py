# Run with: python3 -B drivers/rs485/test_rs485.py
# The whole correctness of this driver is the order things happen in: the direction pin up
# before the bytes, and down only after they have left. So the fakes record one timeline and
# the tests read it back.
import sys, types

clock = [0]
timeline = []


def _sleep_us(us):
    clock[0] += us / 1000
    timeline.append(("wait", us))


sys.modules["time"] = types.SimpleNamespace(
    sleep_us=_sleep_us,
    ticks_ms=lambda: clock[0],
    ticks_diff=lambda a, b: a - b,
)
from rs485 import RS485  # noqa: E402


class _Pin:
    OUT = 3

    def __init__(self):
        self.level = None

    def init(self, mode, value=0):
        self.level = value

    def value(self, level=None):
        if level is None:
            return self.level
        self.level = level
        timeline.append(("de", level))


class _UART:
    """A uart with something at the other end: a reply turns up after a write, not before."""

    def __init__(self, replies=(), waiting=(), txdone=None):
        self.incoming = list(waiting)  # bytes already sitting in the buffer before we start
        self.replies = [list(reply) for reply in replies]
        self._txdone = txdone

    def write(self, data):
        timeline.append(("write", bytes(data)))
        if self.replies:
            self.incoming.extend(self.replies.pop(0))
        return len(data)

    def any(self):
        return len(self.incoming[0]) if self.incoming else 0

    def read(self, count=None):
        return self.incoming.pop(0) if self.incoming else None

    if True:  # only present when the port supports it, which is what the driver checks

        def txdone(self):
            return self._txdone() if self._txdone else True


def link(**kwargs):
    uart = _UART(kwargs.pop("replies", ()), kwargs.pop("waiting", ()))
    de = _Pin()
    bus = RS485(uart, de, **kwargs)
    timeline.clear()  # the timeline is about what happens next, not about setting up
    return bus, uart, de


# Idle listening: a transceiver left talking holds the bus down for everyone.
bus, uart, de = link(baudrate=9600)
assert de.level == 0, "it starts by listening"""

# The order of a send is the whole point.
bus.write(b"hello")
kinds = [entry[0] for entry in timeline]
assert kinds == ["de", "write", "wait", "de"], timeline
assert timeline[0] == ("de", 1), "the line goes up before any bytes"
assert timeline[1] == ("write", b"hello")
assert timeline[-1] == ("de", 0), "and back down at the end"

# How long a byte takes is worked out from the baud rate, not guessed.
assert bus.byte_time_us(1) == 10 * 1_000_000 // 9600, bus.byte_time_us(1)
# Five bytes take five times as long, and the rounding goes the safe way: never less.
assert 0 <= bus.byte_time_us(5) - 5 * bus.byte_time_us(1) < 10, bus.byte_time_us(5)
fast, _, _ = link(baudrate=115200)
assert fast.byte_time_us(1) < bus.byte_time_us(1), "a faster link waits less"
odd, _, _ = link(baudrate=9600, bits_per_byte=11)
assert odd.byte_time_us(1) > bus.byte_time_us(1), "parity makes a byte longer"

# A port that cannot say when it has finished is waited out by the clock instead.
class _PlainUART(_UART):
    txdone = None


timeline.clear()
plain = RS485(_PlainUART(), _Pin(), baudrate=9600)
timeline.clear()
plain.write(b"abcd")
waits = [entry[1] for entry in timeline if entry[0] == "wait"]
assert sum(waits) >= plain.byte_time_us(4), waits
assert waits[-1] == plain.margin_us, "with a margin on the end, because early is what breaks it"

# A port that can say waits for it, and still adds the margin.
answers = [False, False, True]
ready = _UART(txdone=lambda: answers.pop(0) if answers else True)
timeline.clear()
polled = RS485(ready, _Pin(), baudrate=9600)
timeline.clear()
polled.write(b"x")
assert not answers, "it kept asking until the uart said it had finished"
assert timeline[-2] == ("wait", polled.margin_us) and timeline[-1] == ("de", 0)

# The line goes back to listening even if the write itself blows up, or the bus stays deaf.
class _BrokenUART(_UART):
    def write(self, data):
        raise OSError("uart gone")


broken = RS485(_BrokenUART(), _Pin(), baudrate=9600)
try:
    broken.write(b"hi")
    raise AssertionError("the error must not be swallowed")
except OSError:
    pass
assert broken.de.level == 0, "and the bus is released anyway"

# query() sends, then waits for the answer that comes back.
bus, uart, de = link(baudrate=9600, replies=[[b"pong"]])
assert bus.query(b"ping") == b"pong"
assert de.level == 0, "listening again by the time the answer is read"

# Nothing back within the timeout is None, not a hang.
bus, uart, de = link(baudrate=9600)
assert bus.query(b"ping", timeout_ms=5) is None

# A terminator lets a reply arrive in pieces without being cut short.
bus, uart, de = link(baudrate=9600, replies=[[b"par", b"tial\n"]])
assert bus.query(b"?", terminator=b"\n") == b"partial\n"

# Anything left over from a previous exchange is thrown away, not mistaken for this answer.
bus, uart, de = link(baudrate=9600, replies=[[b"fresh"]], waiting=[b"stale"])
assert bus.query(b"?") == b"fresh"

print("rs485: ok")
