# Run with: python3 -B drivers/bh1750/test_bh1750.py
# A fake bus that records command bytes and returns a two byte reading, to check the commands
# and the lux scaling off-board.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from bh1750 import BH1750, CONTINUOUS_HIGH_2, CONTINUOUS_LOW  # noqa: E402


class _I2C:
    def __init__(self, address=0x23):
        self.address = address
        self.commands = []
        self.reading = 0

    def writeto(self, address, data):
        if address != self.address:
            raise OSError(19)  # ENODEV, what MicroPython raises on a NACK
        assert len(data) == 1, "every command is one byte"
        self.commands.append(data[0])

    def readfrom(self, address, length):
        assert address == self.address and length == 2
        return self.reading.to_bytes(2, "big")


# Nothing at the address gives a message that names the part.
try:
    BH1750(_I2C(address=0x5C))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "BH1750" in str(error), error

# Power on, measurement time 69 split as 0x40|1 and 0xB8|5, then continuous high resolution.
bus = _I2C()
sensor = BH1750(bus)
assert bus.commands == [0x01, 0x41, 0xBD, 0x10], [hex(c) for c in bus.commands]

# Readings are big endian, and 1.2 counts are one lux.
bus.reading = 0x04B0  # 1200
assert sensor.light == 1200
assert round(sensor.lux, 3) == 1000.0, sensor.lux

# High resolution mode 2 has half lux steps, so the same count is half the light.
half = BH1750(_I2C(), mode=CONTINUOUS_HIGH_2)
half.i2c.reading = 1200
assert round(half.lux, 3) == 500.0, half.lux

# Doubling the measurement time doubles the counts for the same light.
slow = BH1750(_I2C(), mtreg=138)
assert slow.i2c.commands[1:3] == [0x42, 0xB8 | (138 & 0x3F)], slow.i2c.commands
slow.i2c.reading = 1200
assert round(slow.lux, 3) == 500.0, slow.lux

# The shortest measurement time reaches about 120 000 lux before saturating.
bright = BH1750(_I2C(), mode=CONTINUOUS_LOW, mtreg=31)
assert bright.i2c.commands == [0x01, 0x40, 0xBF, 0x13], [hex(c) for c in bright.i2c.commands]
bright.i2c.reading = 65535
assert 121000 < bright.lux < 122000, bright.lux

# The accuracy is a knob, for calibrating against a light meter.
calibrated = BH1750(_I2C(), accuracy=1.0)
calibrated.i2c.reading = 1200
assert round(calibrated.lux, 3) == 1200.0, calibrated.lux

for bad in ({"mode": 0x20}, {"mtreg": 30}, {"mtreg": 255}):
    try:
        BH1750(_I2C(), **bad)
        raise AssertionError("an unknown setting must be refused: %r" % bad)
    except ValueError:
        pass

print("bh1750: ok")
