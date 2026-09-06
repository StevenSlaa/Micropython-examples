# Run with: python3 -B drivers/eeprom/test_eeprom.py
# A simulated EEPROM that behaves like the real thing in the two ways that matter: a write
# running off the end of a page wraps back to the start of that page, and the chip stops
# answering while it commits. A driver that ignores either loses data on hardware and passes a
# test that only remembers what it was told.
import sys, types

clock = [0]


def _ticks_ms():
    # Every look at the clock moves it on a millisecond, so a polling loop cannot spin forever
    # here any more than it would on a board.
    clock[0] += 1
    return clock[0]


sys.modules["time"] = types.SimpleNamespace(
    ticks_ms=_ticks_ms,
    ticks_add=lambda ticks, delta: ticks + delta,
    ticks_diff=lambda a, b: a - b,
)
from eeprom import DEVICES, EEPROM  # noqa: E402


class _Chip:
    def __init__(self, size=32768, page_size=64, address=0x50, write_polls=3):
        self.size = size
        self.page_size = page_size
        self.address = address
        self.memory = bytearray(b"\xff" * size)
        self.write_polls = write_polls
        self.busy = 0
        self.addrsizes = set()
        self.wrapped = False

    def _check(self, address):
        if address != self.address:
            raise OSError("no device")
        if self.busy:
            self.busy -= 1
            raise OSError("busy")

    def writeto(self, address, data):
        self._check(address)  # an empty write is how the driver asks whether it is ready

    def readfrom_mem(self, address, offset, length, addrsize=8):
        self._check(address)
        self.addrsizes.add(addrsize)
        return bytes(self.memory[offset : offset + length])

    def writeto_mem(self, address, offset, data, addrsize=8):
        self._check(address)
        self.addrsizes.add(addrsize)
        page = offset // self.page_size
        for index, byte in enumerate(data):
            position = offset + index
            if position // self.page_size != page:
                # What the hardware really does: back to the start of this page.
                self.wrapped = True
                position = page * self.page_size + (position % self.page_size)
            self.memory[position] = byte
        self.busy = self.write_polls


def eeprom(**kwargs):
    chip = _Chip(**kwargs)
    return EEPROM(chip, chip.address, chip.size, chip.page_size), chip


# A short write and read back, the easy case.
memory, chip = eeprom()
memory.write(0, b"hello")
assert memory.read(0, 5) == b"hello"
assert chip.addrsizes == {16}, "a 32K device addresses its memory with two bytes"

# A write straddling a page boundary. This is the one that eats data on real hardware.
memory, chip = eeprom(page_size=64)
payload = bytes(range(200))
memory.write(60, payload)
assert not chip.wrapped, "the driver must split writes at the page boundaries"
assert memory.read(60, 200) == payload, "and the bytes must all be where they were put"
assert memory.read(59, 1) == b"\xff", "without disturbing the byte before"
assert memory.read(260, 1) == b"\xff", "or the byte after"

# Proof that the simulation would have caught a driver that did not split: write straight to
# the chip, the way a careless driver would, and watch the data fold back on itself.
chip.writeto_mem(chip.address, 60, bytes(range(200)))
assert chip.wrapped, "the fake chip really does wrap, so the check above means something"

# The driver waits for each write to commit instead of racing the chip.
memory, chip = eeprom(write_polls=3)
memory.write(0, b"abc")
assert chip.busy == 0, "it kept asking until the chip answered"

memory, chip = eeprom(write_polls=10_000)
clock[0] = 0
try:
    memory.write(0, b"x")
    raise AssertionError("a chip that never comes back must raise")
except OSError as error:
    assert "did not finish" in str(error), error

# Small parts address their memory with one byte, and 0x50 is not the only place they live.
memory, chip = eeprom(size=128, page_size=8, address=0x54)
memory.write(120, b"12345678")
assert memory.read(120, 8) == b"12345678"
assert chip.addrsizes == {8}, "a 1K device addresses its memory with one byte"

# Writing past the end is refused rather than wrapping around to the start.
for offset, length in ((124, 8), (128, 1), (-1, 2)):
    try:
        memory.write(offset, b"\x00" * length)
        raise AssertionError("%d bytes at %d must be refused" % (length, offset))
    except ValueError:
        pass
try:
    memory.read(120, 100)
    raise AssertionError("reading past the end must be refused too")
except ValueError:
    pass

# Part numbers, however they are written.
memory, _ = eeprom()
for part, (size, page_size) in DEVICES.items():
    built = EEPROM.for_part(_Chip(), part)
    assert (built.size, built.page_size) == (size, page_size), part
assert EEPROM.for_part(_Chip(), "CAT24C256").size == 32768
assert EEPROM.for_part(_Chip(), "24LC01B").size == 128
try:
    EEPROM.for_part(_Chip(), "something else")
    raise AssertionError("an unknown part must be refused, not guessed at")
except ValueError:
    pass

# fill() is how a region is cleared; an erased EEPROM reads as 0xff.
memory, chip = eeprom(size=256, page_size=8)
memory.write(0, b"secret")
memory.fill(0xFF, 0, 16)
assert memory.read(0, 6) == b"\xff" * 6

print("eeprom: ok")
