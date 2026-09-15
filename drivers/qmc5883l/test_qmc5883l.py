# Run with: python3 -B drivers/qmc5883l/test_qmc5883l.py
# A fake bus of 8 bit registers, to check the control byte, the scaling and the maths off-board.
import sys, types
from struct import pack

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from qmc5883l import (  # noqa: E402
    OVERSAMPLE_64,
    QMC5883L,
    RANGE_2G,
    RATE_10HZ,
    _correction,
)


class _I2C:
    def __init__(self, address=0x0D):
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
    QMC5883L(_I2C(address=0x1E))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "QMC5883L" in str(error), error

# Default: 512x oversampling, 8 gauss, 200Hz, continuous, and the set/reset period written.
bus = _I2C()
sensor = QMC5883L(bus)
assert bus.registers[0x09] == 0x1D, hex(bus.registers[0x09])
assert bus.registers[0x0B] == 0x01

# 3000 counts per gauss at 8 gauss, and a gauss is 100 microtesla.
bus.load(0x00, pack("<hhh", 3000, -3000, 1500))
assert sensor.magnetic == (100.0, -100.0, 50.0), sensor.magnetic

# 2 gauss is 12000 counts per gauss, and every setting lands in its own bits.
fine = QMC5883L(_I2C(), field_range=RANGE_2G, rate=RATE_10HZ, oversample=OVERSAMPLE_64)
assert fine.i2c.registers[0x09] == 0xC1, hex(fine.i2c.registers[0x09])
fine.i2c.load(0x00, pack("<hhh", 12000, 0, -6000))
assert fine.magnetic == (100.0, 0.0, -50.0), fine.magnetic

# Status: bit 0 is data ready, bit 1 overflow.
bus.load(0x06, b"\x01")
assert sensor.ready and not sensor.overflow
bus.load(0x06, b"\x02")
assert sensor.overflow and not sensor.ready

# Heading is measured clockwise from north, and declination shifts it.
bus.load(0x00, pack("<hhh", 3000, 0, 0))
assert round(sensor.heading()) == 0, sensor.heading()
bus.load(0x00, pack("<hhh", 0, 3000, 0))
assert round(sensor.heading()) == 90, sensor.heading()
assert round(sensor.heading(declination=-90)) == 0, "declination is applied"
assert round(sensor.heading(declination=280)) == 10, "and wraps around the circle"

# A hard iron offset is subtracted, a soft iron scale multiplied in afterwards.
shifted = QMC5883L(bus, offset=(0.0, 20.0, 0.0), scale=(1.0, 2.0, 1.0))
assert shifted.magnetic == (0.0, 160.0, 0.0), shifted.magnetic

# Calibration: an axis reading 10..30 is centred on 20, and a narrow axis is stretched to match.
offset, scale = _correction((10.0, -50.0, -10.0), (30.0, 50.0, 10.0))
assert offset == (20.0, 0.0, 0.0), offset
assert [round(value, 3) for value in scale] == [2.333, 0.467, 2.333], scale
assert _correction((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))[1] == (1.0, 1.0, 1.0), "a flat axis is left alone"

for bad in ({"field_range": 0x20}, {"rate": 0x03}, {"oversample": 0x01}):
    try:
        QMC5883L(_I2C(), **bad)
        raise AssertionError("an unknown setting must be refused: %r" % bad)
    except ValueError:
        pass

print("qmc5883l: ok")
