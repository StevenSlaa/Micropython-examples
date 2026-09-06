# Run with: python3 -B drivers/gy271/test_gy271.py
# A fake bus holding both chips, so the register maps and the maths can be checked off-board.
import sys, types
from struct import pack

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from gy271 import HMC5883L, QMC5883L, _correction, compass  # noqa: E402


class _I2C:
    def __init__(self, *addresses):
        self.addresses = list(addresses)
        self.registers = {address: {} for address in addresses}
        self.writes = []

    def scan(self):
        return self.addresses

    def load(self, address, register, data):
        for index, byte in enumerate(data):
            self.registers[address][register + index] = byte

    def readfrom_mem(self, address, register, length):
        stored = self.registers[address]
        return bytes(stored.get(register + index, 0) for index in range(length))

    def writeto_mem(self, address, register, data):
        self.load(address, register, data)
        self.writes.append((address, register, data[0]))


# The right chip is picked off the bus, and configured rather than just read.
assert isinstance(compass(_I2C(0x0D)), QMC5883L), "an HW-246 answers at 0x0d"
assert isinstance(compass(_I2C(0x1E)), HMC5883L), "an older GY-271 answers at 0x1e"
assert isinstance(compass(_I2C(0x0D, 0x1E)), QMC5883L), "the newer chip wins a tie"
try:
    compass(_I2C(0x68))
    raise AssertionError("an empty bus must not return a driver")
except OSError:
    pass

bus = _I2C(0x0D)
qmc = QMC5883L(bus)
assert (0x0D, 0x0B, 0x01) in bus.writes, "the set/reset period register is written"
assert (0x0D, 0x09, 0x1D) in bus.writes, "continuous mode is set"

# 3000 counts per gauss, and a gauss is 100 microtesla: 3000 counts is 100uT.
bus.load(0x0D, 0x00, pack("<hhh", 3000, -3000, 1500))
assert qmc.magnetic == (100.0, -100.0, 50.0), qmc.magnetic
bus.load(0x0D, 0x06, b"\x01")
assert qmc.ready, "the data ready flag is read"

# The HMC stores X, Z, Y big endian; a driver that ignores that swaps two axes.
bus = _I2C(0x1E)
hmc = HMC5883L(bus)
bus.load(0x1E, 0x03, pack(">hhh", 1090, 545, 218))
x, y, z = hmc.magnetic
assert (round(x), round(y), round(z)) == (100, 20, 50), (x, y, z)

# Heading is measured clockwise from north, and declination shifts it.
bus.load(0x1E, 0x03, pack(">hhh", 1090, 0, 0))
assert round(hmc.heading()) == 0, hmc.heading()
bus.load(0x1E, 0x03, pack(">hhh", 0, 0, 1090))  # x=0, y=+1 gauss
assert round(hmc.heading()) == 90, hmc.heading()
assert round(hmc.heading(declination=-90)) == 0, "declination is applied"
assert round(hmc.heading(declination=280)) == 10, "and wraps around the circle"

# A hard iron offset is subtracted, a soft iron scale multiplied in afterwards.
shifted = HMC5883L(bus, offset=(0.0, 20.0, 0.0), scale=(1.0, 2.0, 1.0))
bus.load(0x1E, 0x03, pack(">hhh", 0, 0, 1090))
assert shifted.magnetic == (0.0, 160.0, 0.0), shifted.magnetic

# Calibration: an axis reading 10..30 is centred on 20, and a narrow axis is stretched to match.
offset, scale = _correction((10.0, -50.0, -10.0), (30.0, 50.0, 10.0))
assert offset == (20.0, 0.0, 0.0), offset
# Spans are 10, 50, 10, averaging 23.3: the narrow axes stretch and the wide one shrinks.
assert [round(value, 3) for value in scale] == [2.333, 0.467, 2.333], scale
assert _correction((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))[1] == (1.0, 1.0, 1.0), "a flat axis is left alone"

print("gy271: ok")
