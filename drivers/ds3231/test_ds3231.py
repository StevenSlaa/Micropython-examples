# Run with: python3 -B drivers/ds3231/test_ds3231.py
# A fake DS3231 holding raw register bytes, so the BCD handling and the flag masks can be
# checked against what the datasheet says the chip actually stores.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from ds3231 import DS3231, _from_bcd, _to_bcd  # noqa: E402


class _I2C:
    def __init__(self, registers=None):
        self.registers = dict(registers or {})

    def readfrom_mem(self, address, register, length=1):
        assert address == 0x68
        return bytes(self.registers.get(register + index, 0) for index in range(length))

    def writeto_mem(self, address, register, data):
        assert address == 0x68
        for index, byte in enumerate(data):
            self.registers[register + index] = byte


assert _to_bcd(59) == 0x59 and _from_bcd(0x59) == 59, "binary coded decimal, not hexadecimal"
assert _to_bcd(0) == 0x00 and _from_bcd(0x00) == 0

# 2026-09-06 14:32:07, a Sunday. Weekday 6 is stored as 7, the chip counting from one.
bus = _I2C({0x00: 0x07, 0x01: 0x32, 0x02: 0x14, 0x03: 0x07, 0x04: 0x06, 0x05: 0x09, 0x06: 0x26})
clock = DS3231(bus)
assert clock.datetime == (2026, 9, 6, 14, 32, 7, 6), clock.datetime

# The flag bits that share those registers must not leak into the numbers.
bus.registers[0x05] |= 0x80  # century
bus.registers[0x00] |= 0x80  # unused top bit of seconds
assert clock.datetime[1] == 9 and clock.datetime[5] == 7, "flag bits are masked off"

# Setting the time writes BCD and clears the oscillator stopped flag.
bus = _I2C({0x0F: 0x88})
clock = DS3231(bus)
assert clock.lost_power, "the flag starts set"
clock.datetime = (2026, 12, 31, 23, 59, 58, 3)
assert bus.registers[0x00] == 0x58 and bus.registers[0x01] == 0x59
assert bus.registers[0x02] == 0x23, "24 hour mode, so bit 6 stays clear"
assert bus.registers[0x03] == 0x04, "weekday 3 is stored as 4"
assert bus.registers[0x04] == 0x31 and bus.registers[0x05] == 0x12
assert bus.registers[0x06] == 0x26, "only the last two digits of the year fit"
assert not clock.lost_power, "and the flag is cleared"
assert bus.registers[0x0F] == 0x08, "without disturbing the other status bits"

# The weekday is optional, and defaults to Monday rather than failing.
clock.datetime = (2026, 1, 2, 3, 4, 5)
assert clock.datetime == (2026, 1, 2, 3, 4, 5, 0), clock.datetime

# Temperature is a signed whole degree plus quarters in the top two bits of the second byte.
bus = _I2C()
clock = DS3231(bus)
for raw, expected in (((0x15, 0x40), 21.25), ((0x15, 0xC0), 21.75), ((0x00, 0x00), 0.0)):
    bus.registers[0x11], bus.registers[0x12] = raw
    assert clock.temperature == expected, (raw, clock.temperature)
bus.registers[0x11], bus.registers[0x12] = 0xFB, 0x80  # -5 and a half
assert clock.temperature == -4.5, clock.temperature

# The aging offset is signed, and written back as a byte.
bus.registers[0x10] = 0xFF
assert clock.aging_offset == -1
clock.aging_offset = -20
assert bus.registers[0x10] == 0xEC and clock.aging_offset == -20
clock.aging_offset = 12
assert bus.registers[0x10] == 0x0C

print("ds3231: ok")
