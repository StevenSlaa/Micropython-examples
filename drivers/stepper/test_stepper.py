# Run with: python3 -B drivers/stepper/test_stepper.py
# Fake pins that record every pattern they were given, so the coil sequence can be read back
# exactly as the motor would see it.
import sys, types

waits = []
sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["time"] = types.SimpleNamespace(sleep_us=lambda us: waits.append(us))
from stepper import FULL, HALF, WAVE, StepDirStepper, UnipolarStepper  # noqa: E402


class _Pin:
    OUT = 3

    def __init__(self, coils=None):
        self.level = 0
        self.coils = coils

    def init(self, mode, value=0):
        self.level = value

    def value(self, level=None):
        if level is None:
            return self.level
        self.level = level
        if self.coils is not None:
            self.coils.record()


class _Coils:
    """The four pins together, sampled whenever the last of them changes."""

    def __init__(self):
        self.pins = [_Pin() for _ in range(4)]
        self.pins[-1].coils = self
        self.patterns = []

    def record(self):
        self.patterns.append(tuple(pin.level for pin in self.pins))


def unipolar(**kwargs):
    coils = _Coils()
    return UnipolarStepper(coils.pins, **kwargs), coils


# Half stepping walks the eight patterns in order, and wraps round to the start.
motor, coils = unipolar(steps_per_revolution=4096)
motor.step(9)
assert coils.patterns[:8] == list(HALF[1:]) + [HALF[0]], coils.patterns[:8]
assert coils.patterns[8] == HALF[1], "the ninth step is back to where the second was"
assert motor.position == 9

# Backwards retraces the same patterns the other way, and the position follows.
coils.patterns.clear()
motor.step(-3)
assert coils.patterns == [HALF[0], HALF[7], HALF[6]], coils.patterns
assert motor.position == 6

# Full stepping is four patterns, wave stepping is four different ones.
motor, coils = unipolar(sequence=FULL)
motor.step(4)
assert coils.patterns == list(FULL[1:]) + [FULL[0]]
motor, coils = unipolar(sequence=WAVE)
motor.step(2)
assert coils.patterns == [WAVE[1], WAVE[2]]
assert all(sum(pattern) == 1 for pattern in coils.patterns), "wave energises one coil at a time"
assert all(sum(pattern) == 2 for pattern in FULL), "full stepping energises two"

# Degrees, both ways, on a 28BYJ-48's 4096 half steps per revolution.
motor, coils = unipolar(steps_per_revolution=4096)
motor.step(1024)
assert motor.angle == 90.0, motor.angle
motor.angle = 180
assert motor.position == 2048 and motor.angle == 180.0
motor.angle = 0
assert motor.position == 0, "and back to where it started"

# move_to goes to a position rather than by an amount.
motor.step(100)
motor.move_to(30)
assert motor.position == 30

# Speed is a delay between steps, worked out from the revolutions asked for.
motor, _ = unipolar(steps_per_revolution=4096, rpm=10)
assert motor.step_delay_us == 60_000_000 // (4096 * 10), motor.step_delay_us
motor.rpm = 5
assert motor.step_delay_us == 60_000_000 // (4096 * 5), "slower means a longer wait"

# Releasing turns the coils off, and gives up the holding torque with them.
motor, coils = unipolar()
motor.step(1)
assert any(pin.level for pin in coils.pins), "a stopped stepper is still holding"
motor.release()
assert not any(pin.level for pin in coils.pins)

# A step and direction driver: one pulse per step, and the direction pin set before it.
step_pin, dir_pin, enable_pin = _Pin(), _Pin(), _Pin()
driver = StepDirStepper(step_pin, dir_pin, enable_pin, steps_per_revolution=200)
assert enable_pin.level == 0, "enable is active low on these boards, so this is enabled"
pulses = []
step_pin.value = lambda level, pulses=pulses: pulses.append(level)
driver.step(3)
assert pulses == [1, 0, 1, 0, 1, 0], "three complete pulses"
assert dir_pin.level == 1 and driver.position == 3
driver.step(-1)
assert dir_pin.level == 0, "the direction pin follows the sign"
assert driver.position == 2

# A driver set to sixteenth stepping is told so through steps_per_revolution.
micro = StepDirStepper(_Pin(), _Pin(), steps_per_revolution=200 * 16, rpm=60)
micro.angle = 90
assert micro.position == 800, micro.position

driver.release()
assert enable_pin.level == 1, "and released the other way round"

print("stepper: ok")
