# Driver for a DC motor on an H bridge: the L293D, the L298N module, and anything else wired
# the same way, which includes the DRV8833 and the TB6612.
#
# The chips differ in how much current they pass, how much voltage they drop and whether the
# flyback diodes are built in. None of that is visible from here: to a board they are all two
# direction pins and, usually, an enable pin that takes PWM for the speed.
#
# Two wirings are supported:
#   enable given     the usual one. Direction on IN1 and IN2, speed as PWM on the enable pin.
#   enable is None   for a board whose enable is jumpered high, as L298N modules ship. The PWM
#                    goes on whichever direction pin is driving, which works just as well.

from micropython import const

_FULL = const(65535)


class Motor:
    """One motor on an H bridge.

    `speed` runs from -1.0 for full reverse through 0 for stopped to 1.0 for full forward.

    `reverse=True` swaps which way is forward, for a motor mounted the other way round, so the
    two sides of a robot can take the same numbers. `minimum` is the fraction of full power
    below which the motor only buzzes: with it set, a speed of 0.01 still turns the shaft.
    """

    def __init__(self, in1, in2, enable=None, frequency=1000, reverse=False, minimum=0.0):
        from machine import PWM

        self.reverse = reverse
        self.minimum = minimum
        self._speed = 0.0
        if enable is None:
            # No enable line, so the driving pin carries the PWM and the other one sits low.
            self._enable = None
            self._in1 = PWM(in1)
            self._in2 = PWM(in2)
            self._in1.freq(frequency)
            self._in2.freq(frequency)
        else:
            self._enable = PWM(enable)
            self._enable.freq(frequency)
            self._in1 = in1
            self._in2 = in2
            in1.init(in1.OUT, value=0)
            in2.init(in2.OUT, value=0)
        self.coast()

    def _duty(self, fraction):
        """Turns 0..1 into a duty, leaving room for the minimum the motor needs to move."""
        if fraction <= 0:
            return 0
        if self.minimum:
            fraction = self.minimum + (1.0 - self.minimum) * fraction
        return int(_FULL * min(fraction, 1.0))

    def _drive(self, forward, duty):
        if self._enable is None:
            driving, idle = (self._in1, self._in2) if forward else (self._in2, self._in1)
            idle.duty_u16(0)
            driving.duty_u16(duty)
        else:
            self._in1.value(1 if forward else 0)
            self._in2.value(0 if forward else 1)
            self._enable.duty_u16(duty)

    @property
    def speed(self):
        """-1.0 to 1.0. Reading it gives what was asked for, not what the motor is doing."""
        return self._speed

    @speed.setter
    def speed(self, value):
        value = min(max(value, -1.0), 1.0)
        self._speed = value
        if value == 0:
            self.coast()
            return
        forward = (value > 0) != self.reverse
        self._drive(forward, self._duty(abs(value)))

    def coast(self):
        """Cuts the power and lets the motor spin down on its own."""
        self._speed = 0.0
        if self._enable is None:
            self._in1.duty_u16(0)
            self._in2.duty_u16(0)
        else:
            self._enable.duty_u16(0)
            self._in1.value(0)
            self._in2.value(0)

    def brake(self):
        """Shorts the motor's own windings, which stops it far more sharply than coasting.

        The energy has to go somewhere, and it goes into the bridge as heat. Braking a large
        motor from full speed repeatedly is how an L298N gets too hot to touch.
        """
        self._speed = 0.0
        if self._enable is None:
            self._in1.duty_u16(_FULL)
            self._in2.duty_u16(_FULL)
        else:
            self._in1.value(1)
            self._in2.value(1)
            self._enable.duty_u16(_FULL)
