# Run with: python3 -B drivers/servo/test_servo.py
# A fake PWM channel that reports back the pulse length it was asked for, so the angle and speed
# maths can be checked in the units a datasheet uses: microseconds.
import sys, types


class _PWM:
    def __init__(self, pin):
        self.pin = pin
        self.frequency = None
        self.duty = 0

    def freq(self, value):
        self.frequency = value

    def duty_u16(self, value):
        self.duty = value

    def pulse_us(self):
        """What a scope on the pin would measure."""
        return round(self.duty * (1_000_000 / self.frequency) / 65535)


sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["machine"] = types.SimpleNamespace(PWM=_PWM)
from servo import Servo  # noqa: E402


def servo(**kwargs):
    device = Servo(object(), **kwargs)
    return device, device._pwm


# 50Hz, and nothing sent until it is told something: a servo with no signal is limp on purpose.
device, pwm = servo()
assert pwm.frequency == 50 and pwm.duty == 0
assert device.pulse_us is None and device.angle is None and device.speed is None

# A positional servo: 0, middle and full travel, in the pulse lengths a datasheet quotes.
device.angle = 0
assert pwm.pulse_us() == 500, pwm.pulse_us()
device.angle = 90
assert pwm.pulse_us() == 1500, pwm.pulse_us()
device.angle = 180
assert pwm.pulse_us() == 2500, pwm.pulse_us()
assert round(device.angle) == 180, "and it reads back what it was told"
device.angle = 45
assert round(device.angle) == 45 and pwm.pulse_us() == 1000

# Past either end is clamped, not wrapped: a servo driven past its stop grinds against it.
device.angle = 400
assert round(device.angle) == 180 and pwm.pulse_us() == 2500
device.angle = -90
assert round(device.angle) == 0 and pwm.pulse_us() == 500

# A servo whose travel is not the default, measured rather than assumed.
narrow, pwm = servo(min_us=700, max_us=2300)
narrow.angle = 90
assert pwm.pulse_us() == 1500
narrow.angle = 0
assert pwm.pulse_us() == 700

# A 270 degree servo: the same pulses, spread over more travel.
wide, pwm = servo(angle_range=270)
wide.angle = 270
assert pwm.pulse_us() == 2500
wide.angle = 135
assert pwm.pulse_us() == 1500

# A continuous rotation servo: the middle is stop, and the ends are full speed each way.
spinner, pwm = servo(min_us=1000, max_us=2000)
spinner.speed = 0
assert pwm.pulse_us() == 1500 and spinner.speed == 0.0
spinner.speed = 1
assert pwm.pulse_us() == 2000 and spinner.speed == 1.0
spinner.speed = -1
assert pwm.pulse_us() == 1000 and spinner.speed == -1.0
spinner.speed = 0.5
assert pwm.pulse_us() == 1750, pwm.pulse_us()
spinner.speed = 5
assert pwm.pulse_us() == 2000, "clamped, like the angle"

# A servo that creeps when told to stop is trimmed, and still reaches full speed both ways.
trimmed, pwm = servo(min_us=1000, max_us=2000, stop_us=1480)
trimmed.speed = 0
assert pwm.pulse_us() == 1480, "stop is where it was measured to be"
trimmed.speed = 1
assert pwm.pulse_us() == 2000
trimmed.speed = -1
assert pwm.pulse_us() == 1000
trimmed.speed = 0.5
assert pwm.pulse_us() == 1740, pwm.pulse_us()
assert abs(trimmed.speed - 0.5) < 0.01, "and it reads back symmetrically"

# Releasing stops the pulses, which is different from telling it to stop.
device, pwm = servo()
device.angle = 90
assert pwm.duty > 0
device.release()
assert pwm.duty == 0 and device.angle is None and device.pulse_us is None

# The raw pulse is there for a servo that wants something this driver has no name for.
device.pulse_us = 1234
assert pwm.pulse_us() == 1234

print("servo: ok")
