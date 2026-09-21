# Run with: python3 -B drivers/hmc5883l/test_hmc5883l.py
# A fake bus of 8 bit registers, to check the configuration, the axis order and the maths off-board.
import sys, types
from struct import pack

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from hmc5883l import (  # noqa: E402
    AVERAGE_1,
    HMC5883L,
    RANGE_8_1G,
    RATE_75HZ,
    _correction,
)


class _I2C:
    def __init__(self, address=0x1E):
        self.address = address
        self.registers = {}

    def load(self, register, data):
        for index, byte in enumerate(data):
            self.registers[register + index] = byte

    def readfrom_mem(self, address, register, length):
        assert address == self.address
        return bytes(self.registers.get(register + index, 0) for index in range(length))

    def writeto_mem(self, address, register, data):
        if address != self.address:
            raise OSError(19)  # ENODEV, what MicroPython raises on a NACK
        self.load(register, data)


# Nothing at the address gives a message that names the part.
try:
    HMC5883L(_I2C(address=0x0D))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "HMC5883L" in str(error), error

# Default: 8 samples averaged at 15Hz, 1.3 gauss, continuous.
bus = _I2C()
sensor = HMC5883L(bus)
assert bus.registers[0x00] == 0x70, hex(bus.registers[0x00])
assert bus.registers[0x01] == 0x20, hex(bus.registers[0x01])
assert bus.registers[0x02] == 0x00, hex(bus.registers[0x02])

# The registers hold X, Z, Y big endian; a driver that ignores that swaps two axes.
# 1090 counts per gauss at 1.3 gauss, and a gauss is 100 microtesla.
bus.load(0x03, pack(">hhh", 1090, 545, 218))
x, y, z = sensor.magnetic
assert (round(x), round(y), round(z)) == (100, 20, 50), (x, y, z)
assert not sensor.overflow

# Every setting lands in its own bits, and 8.1 gauss is 230 counts per gauss.
coarse = HMC5883L(_I2C(), field_range=RANGE_8_1G, rate=RATE_75HZ, average=AVERAGE_1)
assert coarse.i2c.registers[0x00] == 0x18, hex(coarse.i2c.registers[0x00])
assert coarse.i2c.registers[0x01] == 0xE0, hex(coarse.i2c.registers[0x01])
coarse.i2c.load(0x03, pack(">hhh", 230, 0, -115))
assert coarse.magnetic == (100.0, -50.0, 0.0), coarse.magnetic

# The chip writes -4096 into a clipped axis.
bus.load(0x03, pack(">hhh", 0, -4096, 0))
sensor.magnetic
assert sensor.overflow

# Status bit 0 is data ready.
bus.load(0x09, b"\x01")
assert sensor.ready

# Heading is measured clockwise from north, and declination shifts it.
bus.load(0x03, pack(">hhh", 1090, 0, 0))
assert round(sensor.heading()) == 0, sensor.heading()
bus.load(0x03, pack(">hhh", 0, 0, 1090))  # x=0, y=+1 gauss
assert round(sensor.heading()) == 90, sensor.heading()
assert round(sensor.heading(declination=-90)) == 0, "declination is applied"
assert round(sensor.heading(declination=280)) == 10, "and wraps around the circle"

# A hard iron offset is subtracted, a soft iron scale multiplied in afterwards.
shifted = HMC5883L(bus, offset=(0.0, 20.0, 0.0), scale=(1.0, 2.0, 1.0))
bus.load(0x03, pack(">hhh", 0, 0, 1090))
assert shifted.magnetic == (0.0, 160.0, 0.0), shifted.magnetic

# Calibration: an axis reading 10..30 is centred on 20, and a narrow axis is stretched to match.
offset, scale = _correction((10.0, -50.0, -10.0), (30.0, 50.0, 10.0))
assert offset == (20.0, 0.0, 0.0), offset
assert [round(value, 3) for value in scale] == [2.333, 0.467, 2.333], scale
assert _correction((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))[1] == (1.0, 1.0, 1.0), "a flat axis is left alone"

for bad in ({"field_range": 0x10}, {"rate": 0x1C}, {"average": 0x01}):
    try:
        HMC5883L(_I2C(), **bad)
        raise AssertionError("an unknown setting must be refused: %r" % bad)
    except ValueError:
        pass

print("hmc5883l: ok")
