# Driver for hobby servos, the three wire kind: SG90, MG996R, DM-S0306D, TS90M and the rest.
#
# All of them listen to the same thing: a pulse, repeated 50 times a second, whose *length*
# carries the instruction. Not the duty cycle, which is what makes a servo the odd one out among
# everything else driven by PWM. Around 1.5ms is the middle, and roughly 1ms and 2ms are the
# ends of the travel.
#
# What the servo does with that depends on which kind it is:
#
#   positional    the usual sort, which turns to an angle and holds it. Use `angle`.
#   continuous    a 360 degree servo, whose electronics have been changed so the same signal
#                 sets a speed and a direction instead. Middle means stop. Use `speed`.
#
# Both are the same signal and the same class here, because they are the same hardware.

from micropython import const

_FULL = const(65535)


class Servo:
    """A servo on `pin`.

    `min_us` and `max_us` are the pulse lengths at the two ends of its travel, and they are
    worth measuring rather than trusting. The 500 to 2500 default reaches the full sweep of most
    positional servos; the older 1000 to 2000 is what the datasheets say and usually falls short
    of both ends.

    For a continuous rotation servo, pass `min_us=1000, max_us=2000`: it has no travel to reach,
    and a longer pulse than it expects only makes it strain.
    """

    def __init__(self, pin, frequency=50, min_us=500, max_us=2500, angle_range=180, stop_us=None):
        from machine import PWM

        self._pwm = PWM(pin)
        self._pwm.freq(frequency)
        self.period_us = 1_000_000 // frequency
        self.min_us = min_us
        self.max_us = max_us
        self.angle_range = angle_range
        # Where a continuous rotation servo stands still. It is rarely exactly the middle: a
        # servo that creeps when told to stop wants this trimmed by a few tens of microseconds.
        self.stop_us = (min_us + max_us) // 2 if stop_us is None else stop_us
        self._pulse_us = None
        self.release()

    @property
    def pulse_us(self):
        """The pulse length being sent, in microseconds, or None while released."""
        return self._pulse_us

    @pulse_us.setter
    def pulse_us(self, microseconds):
        microseconds = min(max(int(microseconds), self.min_us), self.max_us)
        self._pulse_us = microseconds
        self._pwm.duty_u16(microseconds * _FULL // self.period_us)

    @property
    def angle(self):
        """Where a positional servo has been told to stand, in degrees. None while released."""
        if self._pulse_us is None:
            return None
        span = self.max_us - self.min_us
        return (self._pulse_us - self.min_us) * self.angle_range / span

    @angle.setter
    def angle(self, degrees):
        degrees = min(max(degrees, 0), self.angle_range)
        span = self.max_us - self.min_us
        self.pulse_us = self.min_us + span * degrees / self.angle_range

    @property
    def speed(self):
        """How fast a continuous rotation servo has been told to turn, -1.0 to 1.0."""
        if self._pulse_us is None:
            return None
        if self._pulse_us >= self.stop_us:
            reach = self.max_us - self.stop_us
            return (self._pulse_us - self.stop_us) / reach if reach else 0.0
        reach = self.stop_us - self.min_us
        return (self._pulse_us - self.stop_us) / reach if reach else 0.0

    @speed.setter
    def speed(self, value):
        value = min(max(value, -1.0), 1.0)
        # Measured out from the stop point in each direction, so a trimmed stop still reaches
        # full speed both ways.
        reach = (self.max_us - self.stop_us) if value >= 0 else (self.stop_us - self.min_us)
        self.pulse_us = self.stop_us + value * reach

    def release(self):
        """Stops sending pulses.

        A servo given no signal stops holding: a positional one can be turned by hand and stops
        buzzing and drawing current, and a continuous one coasts to a halt. This is not the same
        as telling a continuous servo to stop, which keeps it actively resisting being turned.
        """
        self._pulse_us = None
        self._pwm.duty_u16(0)
