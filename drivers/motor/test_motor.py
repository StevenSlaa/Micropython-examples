# Run with: python3 -B drivers/motor/test_motor.py
# Fake pins and PWM channels, so what the bridge would actually see can be read back for both
# wirings: with an enable pin, and with the enable jumpered high.
import sys, types

FULL = 65535


class _Pin:
    OUT = 3

    def __init__(self, name):
        self.name = name
        self.level = None

    def init(self, mode, value=None):
        self.level = value

    def value(self, level=None):
        if level is None:
            return self.level
        self.level = level


class _PWM:
    def __init__(self, pin):
        self.pin = pin
        self.duty = None
        self.frequency = None

    def freq(self, value):
        self.frequency = value

    def duty_u16(self, value):
        self.duty = value


sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["machine"] = types.SimpleNamespace(PWM=_PWM)
from motor import Motor  # noqa: E402


def with_enable(**kwargs):
    in1, in2, enable = _Pin("in1"), _Pin("in2"), _Pin("en")
    return Motor(in1, in2, enable, **kwargs), in1, in2


def without_enable(**kwargs):
    return Motor(_Pin("in1"), _Pin("in2"), **kwargs)


# The usual wiring: direction on the two pins, speed as PWM on the enable.
motor, in1, in2 = with_enable()
assert motor._enable.frequency == 1000, "the enable pin carries the PWM"
assert motor._enable.duty == 0 and in1.level == 0 and in2.level == 0, "stopped to start with"

motor.speed = 1.0
assert (in1.level, in2.level) == (1, 0) and motor._enable.duty == FULL
motor.speed = -0.5
assert (in1.level, in2.level) == (0, 1), "the pins swap for the other direction"
assert motor._enable.duty == FULL // 2, motor._enable.duty
assert motor.speed == -0.5

# Speeds outside the range are clamped rather than wrapping round to full reverse.
motor.speed = 5
assert motor.speed == 1.0 and motor._enable.duty == FULL
motor.speed = -5
assert motor.speed == -1.0 and (in1.level, in2.level) == (0, 1)

# Coasting cuts the power; braking shorts the windings, which is a different thing entirely.
motor.speed = 0
assert motor._enable.duty == 0 and (in1.level, in2.level) == (0, 0), "coasted"
motor.speed = 0.8
motor.brake()
assert (in1.level, in2.level) == (1, 1) and motor._enable.duty == FULL, "both sides high"
assert motor.speed == 0.0

# reverse=True swaps which way is forward, so both sides of a robot take the same numbers.
mirrored, in1, in2 = with_enable(reverse=True)
mirrored.speed = 1.0
assert (in1.level, in2.level) == (0, 1), "forward drives the other way round"
assert mirrored.speed == 1.0, "but it still reads as forward"

# minimum lifts the bottom of the range past where the motor only buzzes.
lively, _, _ = with_enable(minimum=0.4)
lively.speed = 0.0001
assert lively._enable.duty > int(FULL * 0.4), lively._enable.duty
lively.speed = 1.0
assert lively._enable.duty == FULL, "and full speed is still full speed"
lively.speed = 0
assert lively._enable.duty == 0, "while zero is still off"

# The other wiring: enable jumpered high, so the PWM has to go on the driving pin.
jumpered = without_enable()
assert jumpered._enable is None
assert jumpered._in1.frequency == 1000 and jumpered._in2.frequency == 1000
jumpered.speed = 0.5
assert jumpered._in1.duty == FULL // 2 and jumpered._in2.duty == 0
jumpered.speed = -1.0
assert jumpered._in2.duty == FULL and jumpered._in1.duty == 0, "the other pin drives"
jumpered.coast()
assert jumpered._in1.duty == 0 and jumpered._in2.duty == 0
jumpered.brake()
assert jumpered._in1.duty == FULL and jumpered._in2.duty == FULL, "both pins high is a brake"

print("motor: ok")
