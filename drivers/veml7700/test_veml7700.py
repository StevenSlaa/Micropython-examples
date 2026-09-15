# Run with: python3 -B drivers/veml7700/test_veml7700.py
# A fake bus of 16 bit little endian registers, to check the bit packing and the lux scaling.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
from veml7700 import GAIN_1_8, GAIN_2, IT_25MS, IT_800MS, VEML7700  # noqa: E402


class _I2C:
    def __init__(self, address=0x10):
        self.address = address
        self.registers = {0x00: 0x0001}  # powers up shut down

    def readfrom_mem(self, address, register, length):
        assert address == self.address and length == 2
        return self.registers.get(register, 0).to_bytes(2, "little")

    def writeto_mem(self, address, register, data):
        if address != self.address:
            raise OSError(19)  # ENODEV, what MicroPython raises on a NACK
        assert len(data) == 2, "registers are 16 bit words"
        self.registers[register] = int.from_bytes(data, "little")


# Nothing at the address gives a message that names the part.
try:
    VEML7700(_I2C(address=0x48))
    raise AssertionError("an empty address must be reported")
except OSError as error:
    assert "VEML7700" in str(error), error

bus = _I2C()
sensor = VEML7700(bus)
# Gain 1/4 in bits 12:11, 100ms is a zero code, and the shutdown bit is cleared.
assert bus.registers[0x00] == 0x1800, hex(bus.registers[0x00])

# Readings are little endian words from two separate registers.
bus.registers[0x04] = 1000
bus.registers[0x05] = 1500
assert sensor.light == 1000 and sensor.white == 1500

# At gain 2 and 800ms a count is 0.0042 lux; gain 1/4 and 100ms are 8x each, so 0.2688.
assert round(sensor.lux, 3) == 268.8, sensor.lux

sensor.gain = GAIN_2
sensor.integration_time = IT_800MS
assert bus.registers[0x00] == 0x08C0, hex(bus.registers[0x00])
assert round(sensor.lux, 3) == 4.2, sensor.lux

# The least sensitive setting reaches about 140 000 lux, and stays sane there.
sensor.gain = GAIN_1_8
sensor.integration_time = IT_25MS
assert bus.registers[0x00] == 0x1300, hex(bus.registers[0x00])
bus.registers[0x04] = 65535
assert 140000 < sensor.lux < 141000, sensor.lux

# The resolution is a knob, for calibrating against a meter or following the older datasheet.
old = VEML7700(_I2C(), gain=GAIN_2, integration_time=IT_800MS, resolution=0.0036)
old.i2c.registers[0x04] = 1000
assert round(old.lux, 3) == 3.6, old.lux

for bad in ({"gain": 7}, {"integration_time": 0x05}):
    try:
        VEML7700(_I2C(), **bad)
        raise AssertionError("an unknown setting must be refused: %r" % bad)
    except ValueError:
        pass
try:
    sensor.integration_time = 0x04
    raise AssertionError("an unknown integration time must be refused")
except ValueError:
    pass
assert bus.registers[0x00] == 0x1300, "and leaves the sensor as it was"

print("veml7700: ok")
