# Run with: python3 -B drivers/vl6180x/test_vl6180x.py
# Stubs the firmware modules and drives a fake sensor, including the paths that only show up
# when the hardware misbehaves.
import sys, types

clock = [0]
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["time"] = types.SimpleNamespace(
    sleep_ms=lambda ms: clock.__setitem__(0, clock[0] + ms),
    ticks_ms=lambda: clock[0],
    ticks_add=lambda ticks, delta: ticks + delta,
    ticks_diff=lambda a, b: a - b,
)
from vl6180x import GAIN_1, GAIN_10, VL6180X, _STARTUP  # noqa: E402


class _I2C:
    """A VL6180X that reports a sample is ready as soon as a measurement is started."""

    def __init__(self, model=0xB4, fresh=0x01, responsive=True):
        self.registers = {0x000: model, 0x016: fresh, 0x04F: 0x00}
        self.writes = []
        self.responsive = responsive

    def readfrom_mem(self, address, register, length, addrsize=8):
        assert addrsize == 16, "the VL6180X has 16 bit register addresses"
        assert address == 0x29
        value = self.registers.get(register, 0)
        return value.to_bytes(length, "big")

    def writeto_mem(self, address, register, data, addrsize=8):
        assert addrsize == 16
        self.registers[register] = data[0]
        self.writes.append((register, data[0]))
        if not self.responsive:
            return
        if register == 0x018:  # a range measurement was started
            self.registers[0x04F] = 0x04
        elif register == 0x038:  # a light measurement was started
            self.registers[0x04F] = 0x04 << 3
        elif register == 0x015:  # interrupts cleared
            self.registers[0x04F] = 0x00


bus = _I2C()
sensor = VL6180X(bus)
assert bus.writes[: len(_STARTUP)] == list(_STARTUP), "the whole start-up sequence is written"
assert (0x016, 0x00) in bus.writes, "the fresh out of reset flag is cleared afterwards"

# The tuning is written even to a sensor that has already been through it, because the flag
# stays clear while the sensor keeps its power and the board reboots without it.
warm = _I2C(fresh=0x00)
VL6180X(warm)
assert warm.writes[: len(_STARTUP)] == list(_STARTUP), "a warm sensor is tuned again"

# The wrong chip at that address is caught rather than read as nonsense.
try:
    VL6180X(_I2C(model=0x00))
    raise AssertionError("a foreign device must be rejected")
except OSError:
    pass

bus.registers[0x062] = 47
assert sensor.range == 47, "millimetres are read straight out of the register"
assert (0x015, 0x07) in bus.writes, "the interrupt is cleared after a reading"
shifted = VL6180X(_I2C())
shifted.i2c.registers[0x062] = 47
shifted.offset = -3
assert shifted.range == 44, "the offset trims the reading"

bus.registers[0x04D] = 0xB0  # status is the top nibble
assert sensor.range_status == 11, "the status nibble is shifted down"

# 0.32 lux per count at gain 1, and ten times the gain is a tenth of the lux.
bus.registers[0x050] = 1000
assert round(sensor.lux(GAIN_1), 2) == 320.0, sensor.lux(GAIN_1)
assert round(sensor.lux(GAIN_10), 2) == 32.0, sensor.lux(GAIN_10)
assert (0x03F, 0x40 | GAIN_10) in bus.writes, "the gain register keeps its enable bit"
try:
    sensor.lux(gain=99)
    raise AssertionError("an unknown gain must be refused")
except ValueError:
    pass

# Convergence time is the knob for a weak return, and the register only holds 1 to 63.
sensor.convergence_time = 63
assert bus.registers[0x01C] == 63 and sensor.convergence_time == 63
sensor.convergence_time = 200
assert bus.registers[0x01C] == 63, "an out of range value is clamped, not truncated"
sensor.convergence_time = 0
assert bus.registers[0x01C] == 1

# The part to part offset register is signed.
sensor.part_to_part_offset = -4
assert bus.registers[0x024] == 0xFC and sensor.part_to_part_offset == -4

# A sensor that never reports a sample gives up instead of hanging the board forever.
stuck = VL6180X(_I2C(), timeout=50)
stuck.i2c.responsive = False
try:
    stuck.range
    raise AssertionError("a silent sensor must time out")
except OSError as error:
    assert "in time" in str(error), error

print("vl6180x: ok")
