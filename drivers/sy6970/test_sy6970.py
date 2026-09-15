# Run with: python3 -B drivers/sy6970/test_sy6970.py
# A fake bus of byte registers, filled with values read from a T-Display-S3 Long's SY6970.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from sy6970 import SY6970  # noqa: E402


class _I2C:
    def __init__(self, address=0x6A):
        self.address = address
        # measured with USB power and no battery: registers 0x00 to 0x14
        self.registers = dict(enumerate(bytes.fromhex("48061d1a20135e9d034473a7081500443d9a00080c")))

    def readfrom_mem(self, address, register, length):
        if address != self.address:
            raise OSError(19)  # ENODEV, what MicroPython raises on a NACK
        assert length == 1
        return bytes((self.registers[register],))

    def writeto_mem(self, address, register, data):
        assert address == self.address and len(data) == 1
        self.registers[register] = data[0]


# Nothing at the address gives a message that names the part.
try:
    SY6970(_I2C(address=0x6B))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "SY6970" in str(error), error

# Setup switches measuring on and the watchdog off, and changes no other bits.
bus = _I2C()
charger = SY6970(bus)
assert bus.registers[0x02] == 0xDD and bus.registers[0x07] == 0x8D, (hex(bus.registers[0x02]), hex(bus.registers[0x07]))
kept = _I2C()
SY6970(kept, watchdog=True)
assert kept.registers[0x07] == 0x9D

# Readings, as they came off the board: USB host input, 5.2 V in, 3.66 V system, no battery.
assert charger.input == "adapter" and charger.power_good
assert charger.input_voltage == 5200 and charger.system_voltage == 3664
assert charger.battery_voltage == 0 and charger.charge_state == "not charging" and charger.charge_current == 0
bus.registers[0x0E] = 0x5F
assert charger.battery_voltage == 4204
bus.registers[0x11] = 0x1A  # VBUS_GD clear: no input
assert charger.input_voltage == 0

# A charging battery reports its current; when charging stops, the stale register is ignored.
bus.registers[0x0B] = 0xB6
bus.registers[0x12] = 0x14
assert charger.charge_state == "fast charging" and charger.charge_current == 1000
bus.registers[0x0B] = 0xA7
assert charger.charge_current == 0

# Settings touch only their own bits, round down to the chip's steps, and clamp to its range.
charger.charge_enabled = False
assert bus.registers[0x03] == 0x0A and not charger.charge_enabled
charger.charge_enabled = True
assert bus.registers[0x03] == 0x1A and charger.charge_enabled
bus.registers[0x04] = 0x80 | 0x20
charger.charge_current_limit = 500
assert bus.registers[0x04] == 0x80 | 7 and charger.charge_current_limit == 448
charger.charge_current_limit = 99999
assert charger.charge_current_limit == 5056 and bus.registers[0x04] & 0x80
charger.input_current_limit = 500
assert bus.registers[0x00] == 0x40 | 8 and charger.input_current_limit == 500
charger.input_current_limit = 10
assert charger.input_current_limit == 100
charger.charge_voltage = 4208
assert bus.registers[0x06] == 23 << 2 | 0x02 and charger.charge_voltage == 4208
charger.charge_voltage = 5000
assert charger.charge_voltage == 4608

bus.registers[0x0C] = 0x88
assert charger.faults == 0x88

print("sy6970: ok")
