# Run with: python3 -B drivers/vcnl4040/test_vcnl4040.py
# A fake bus of 16 bit little endian registers, to check the bit packing and the lux scaling.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from vcnl4040 import (  # noqa: E402
    ALS_80MS,
    ALS_640MS,
    DUTY_1_80,
    LED_50MA,
    LED_200MA,
    VCNL4040,
)


class _I2C:
    def __init__(self, device_id=0x0186):
        self.registers = {0x0C: device_id}

    def readfrom_mem(self, address, register, length):
        assert address == 0x60 and length == 2
        return self.registers.get(register, 0).to_bytes(2, "little")

    def writeto_mem(self, address, register, data):
        assert address == 0x60 and len(data) == 2, "registers are 16 bit words"
        self.registers[register] = int.from_bytes(data, "little")


# A different chip at 0x60 is caught rather than read as nonsense.
try:
    VCNL4040(_I2C(device_id=0x0000))
    raise AssertionError("a foreign device must be rejected")
except OSError:
    pass

bus = _I2C()
sensor = VCNL4040(bus)
# Ambient light enabled at 80ms: shutdown bit clear, integration time zero.
assert bus.registers[0x00] == 0x0000, hex(bus.registers[0x00])
# Proximity enabled, 1/40 duty, 8T integration, 12 bit output.
assert bus.registers[0x03] == 0x000E, hex(bus.registers[0x03])
# 200mA in the high byte of PS_CONF3/PS_MS, and the white channel left enabled.
assert bus.registers[0x04] == 0x0700, hex(bus.registers[0x04])

high = VCNL4040(_I2C(), duty=DUTY_1_80, led_current=LED_50MA, high_resolution=True)
assert high.i2c.registers[0x03] == 0x084E, hex(high.i2c.registers[0x03])
assert high.i2c.registers[0x04] == 0x0000, "50mA is a zero field, not a missing write"

# Readings are little endian words from three separate registers.
bus.registers[0x08] = 1234
bus.registers[0x09] = 500
bus.registers[0x0A] = 777
assert sensor.proximity == 1234 and sensor.light == 500 and sensor.white == 777

# Lux is 0.1 per step at 80ms, and each longer integration time halves that.
assert round(sensor.lux, 3) == 50.0, sensor.lux
sensor.integration_time = ALS_640MS
assert round(sensor.lux, 4) == 6.25, sensor.lux
assert bus.registers[0x00] == 0x00C0, "the integration time is written to its own bits"
sensor.integration_time = ALS_80MS
assert bus.registers[0x00] == 0x0000, "and cleared again without disturbing the rest"
try:
    sensor.integration_time = 9
    raise AssertionError("an unknown integration time must be refused")
except ValueError:
    pass

# The LED current shares its register with settings that must survive a change.
bus.registers[0x04] = 0x0700 | 0x0010
sensor.led_current = LED_50MA
assert bus.registers[0x04] == 0x0010, hex(bus.registers[0x04])
sensor.led_current = LED_200MA
assert sensor.led_current == LED_200MA and bus.registers[0x04] == 0x0710

# Crosstalk cancellation is a plain 16 bit value.
sensor.cancellation = 320
assert bus.registers[0x05] == 320 and sensor.cancellation == 320

print("vcnl4040: ok")
