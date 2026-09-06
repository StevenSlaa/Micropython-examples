# Run with: python3 drivers/tc74/test_tc74.py
# A fake I2C bus, so the register handling can be checked without a sensor.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from tc74 import TC74  # noqa: E402


class _I2C:
    def __init__(self, temp=0, config=0):
        self.registers = {0x00: temp, 0x01: config}
        self.writes = []

    def readfrom_mem(self, address, register, length):
        assert address == 0x4A and length == 1
        return bytes([self.registers[register]])

    def writeto_mem(self, address, register, data):
        self.registers[register] = data[0]
        self.writes.append((register, data[0]))


bus = _I2C(temp=25)
sensor = TC74(bus, address=0x4A)
assert sensor.temperature == 25, "a positive reading"

bus.registers[0x00] = 0xFF
assert sensor.temperature == -1, "0xff is minus one, not 255"
bus.registers[0x00] = 0xBF
assert sensor.temperature == -65, "the bottom of the range"
bus.registers[0x00] = 0x7F
assert sensor.temperature == 127, "the top of the range"

assert TC74(bus, address=0x4A, offset=-3).temperature == 124, "the offset trims the reading"

bus.registers[0x01] = 0x40
assert sensor.ready and not sensor.standby, "data ready, running"
bus.registers[0x01] = 0x80
assert sensor.standby and not sensor.ready, "standby, no reading yet"

bus.registers[0x01] = 0x40
sensor.standby = True
assert bus.writes[-1] == (0x01, 0xC0), "standby is set without losing the other bits"
sensor.standby = False
assert bus.writes[-1] == (0x01, 0x40), "and cleared again"

print("tc74: ok")
