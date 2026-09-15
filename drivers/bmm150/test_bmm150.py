# Run with: python3 -B drivers/bmm150/test_bmm150.py
# A fake BMM150 with its trim registers filled in, to check the power up, the bit unpacking and the
# compensation off-board. The trim values are chosen so the answers can be worked out by hand.
import math, sys, types
from struct import pack

clock = [0]


def _sleep_ms(ms):
    clock[0] += ms


sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["time"] = types.SimpleNamespace(
    sleep_ms=_sleep_ms,
    ticks_ms=lambda: clock[0],
    ticks_add=lambda ticks, delta: ticks + delta,
    ticks_diff=lambda end, start: end - start,
)
from bmm150 import BMM150, HIGH_ACCURACY, RATE_20HZ, _correction  # noqa: E402


class _I2C:
    def __init__(self, address=0x10, chip_id=0x32, x1=0, x2=0, xy1=0, asleep_reads=0, refused_writes=0):
        self.address = address
        self.registers = {0x40: chip_id}
        self.writes = []
        # How many reads a slow chip fails while it wakes up.
        self.asleep_reads = asleep_reads
        # How many writes fail first, like the first transaction on a new SoftI2C on a Pico.
        self.refused_writes = refused_writes
        # With RHALL equal to xyz1 the X and Y temperature terms vanish, leaving
        # x = raw * (160 + x2) / 512 + x1 / 2, and z = (raw - z4) * 2048 / (z2 + z1 * rhall / 32768).
        self.load(0x5D, pack("<bb", x1, x1))
        self.load(0x62, pack("<hbb", 0, x2, x2))
        # z2=400, z1=30720, xyz1=6400 with the unrelated top bit set, z3=0, xy2=0.
        self.load(0x68, pack("<hHHhbB", 400, 30720, 6400 | 0x8000, 0, 0, xy1))

    def load(self, register, data):
        for index, byte in enumerate(data):
            self.registers[register + index] = byte

    def reading(self, x, y, z, rhall=6400, ready=True):
        # The spare low bits are set on purpose: they are flags, not part of the value.
        self.load(0x42, pack("<hhhH", (x << 3) | 0b101, (y << 3) | 0b101, (z << 1) | 1, (rhall << 2) | ready))

    def readfrom_mem(self, address, register, length):
        if address != self.address:
            raise OSError(19)  # ENODEV, what MicroPython raises on a NACK
        if self.asleep_reads:
            self.asleep_reads -= 1
            raise OSError(19)
        # Suspended, the chip reads as zeros until the power bit is set.
        powered = self.registers.get(0x4B, 0) & 0x01
        return bytes(self.registers.get(register + i, 0) if powered else 0 for i in range(length))

    def writeto_mem(self, address, register, data):
        if address != self.address:
            raise OSError(19)
        if self.refused_writes:
            self.refused_writes -= 1
            raise OSError(19)
        self.load(register, data)
        self.writes.append((register, data[0]))


# Nothing at the address, and something that is not a BMM150, are both reported by name.
try:
    BMM150(_I2C(address=0x13))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "No BMM150" in str(error), error
try:
    BMM150(_I2C(chip_id=0x00))
    raise AssertionError("a wrong chip id must be reported")
except OSError as error:
    assert "not a BMM150" in str(error), error

# A bus that refuses the first write, as a new SoftI2C on a Pico does, is retried, and the power
# on still comes first.
fresh = BMM150(_I2C(refused_writes=1))
assert fresh.i2c.writes == [(0x4B, 0x01), (0x51, 0x04), (0x52, 0x0E), (0x4C, 0x00)], fresh.i2c.writes

# A chip slow to wake, failing the first reads after power on, is waited for.
slow = BMM150(_I2C(asleep_reads=3))
assert slow.i2c.writes[0] == (0x4B, 0x01)

# One that answers its address but never its id says exactly that, not "No BMM150".
try:
    BMM150(_I2C(asleep_reads=100))
    raise AssertionError("a chip that never wakes must be reported")
except OSError as error:
    assert "answered, but gave no chip id" in str(error) and "19" in str(error), error

# Powered first, since a suspended chip hides its id; then the preset and normal mode at 10Hz.
bus = _I2C()
sensor = BMM150(bus)
assert bus.writes == [(0x4B, 0x01), (0x51, 0x04), (0x52, 0x0E), (0x4C, 0x00)], bus.writes
assert sensor._xyz1 == 6400, "the top bit of xyz1 is masked off"

accurate = BMM150(_I2C(), preset=HIGH_ACCURACY, rate=RATE_20HZ)
assert accurate.i2c.writes[1:] == [(0x51, 0x17), (0x52, 0x52), (0x4C, 0x28)], accurate.i2c.writes

# Untrimmed X and Y are 160/512 = 0.3125uT a count, and signed. Z: 2048 / (400 + 6000) = 0.32.
bus.reading(320, -320, 625)
assert sensor._raw() == (320, -320, 625, 6400), sensor._raw()
x, y, z = sensor.magnetic
assert (round(x, 6), round(y, 6), round(z, 6)) == (100.0, -100.0, 200.0), (x, y, z)
assert sensor.ready

# Trim values are signed bytes: x2=96 makes it raw/2, x1=-8 subtracts 4.
trimmed = BMM150(_I2C(x1=-8, x2=96))
trimmed.i2c.reading(320, 320, 625)
x, y, _ = trimmed.magnetic
assert (round(x, 6), round(y, 6)) == (156.0, 156.0), (x, y)

# RHALL takes part through xy1. At rhall = xyz1/2 the term is 16384 * xy1 / 16384 = 128, so
# x = 320 * (128 + 256) * 160 / 8192 / 16 = 150.
warm = BMM150(_I2C(xy1=128))
warm.i2c.reading(320, 320, 625, rhall=3200)
assert round(warm.magnetic[0], 6) == 150.0, warm.magnetic
# And in Z through z1: the divisor becomes 400 + 30720 * 3200 / 32768 = 3400.
assert round(warm.magnetic[2], 6) == round(625 * 2048 / 3400, 6), warm.magnetic

# Overflowed axes, and a sample with no RHALL yet, come back as nan rather than a plausible 0.
bus.reading(-4096, 320, -16384)
x, y, z = sensor.magnetic
assert math.isnan(x) and not math.isnan(y) and math.isnan(z), (x, y, z)
bus.reading(320, 320, 625, rhall=0, ready=False)
assert all(math.isnan(value) for value in sensor.magnetic) and not sensor.ready

# Heading is measured clockwise from north, and declination shifts it.
bus.reading(320, 0, 0)
assert round(sensor.heading()) == 0, sensor.heading()
bus.reading(0, 320, 0)
assert round(sensor.heading()) == 90, sensor.heading()
assert round(sensor.heading(declination=280)) == 10, "declination wraps around the circle"

# Calibration over a steady field centres it on zero, and leaves the scale alone.
bus.reading(320, -320, 625)
offset, scale = sensor.calibrate(seconds=1)
assert [round(v, 6) for v in offset] == [100.0, -100.0, 200.0] and scale == (1.0, 1.0, 1.0)
assert [round(v, 6) for v in sensor.magnetic] == [0.0, 0.0, 0.0]

offset, scale = _correction((10.0, -50.0, -10.0), (30.0, 50.0, 10.0))
assert offset == (20.0, 0.0, 0.0), offset
assert [round(value, 3) for value in scale] == [2.333, 0.467, 2.333], scale

try:
    BMM150(_I2C(), rate=0x01)
    raise AssertionError("an unknown rate must be refused")
except ValueError:
    pass

print("bmm150: ok")
