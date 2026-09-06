# Driver for stepper motors, which turn a fixed fraction of a revolution per step rather than
# spinning while power is applied. That is what makes them worth the trouble: no feedback is
# needed to know where the shaft is, as long as nothing has stopped it.
#
# Two ways of wiring one are covered, because both are common:
#
#   UnipolarStepper   four pins straight to the coils, through a ULN2003 board or an H bridge.
#                     The 28BYJ-48 and its little blue ULN2003 board are this. The driver walks
#                     the coils through their sequence itself.
#
#   StepDirStepper    two pins to a step and direction driver: A4988, DRV8825, TMC2208 and the
#                     rest. The board does the coil work; a pulse on one pin is one step.

from micropython import const
from time import sleep_us

# One coil energised at a time. Least torque and least current, and it can miss steps.
WAVE = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
# Two coils at a time: about 40% more torque for twice the current. The usual choice.
FULL = ((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1), (1, 0, 0, 1))
# Alternating one and two, which halves the step size. Smoother and quieter, half the speed.
HALF = (
    (1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0),
    (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1), (1, 0, 0, 1),
)

_MINUTE_US = const(60_000_000)


class Stepper:
    """Shared bookkeeping: where the shaft is, how fast to move, and how to talk in degrees.

    `position` is counted in steps from wherever the motor was when the program started, which
    is the only zero a stepper has. It is not measured: if something stops the shaft, the motor
    misses steps and the count quietly becomes a lie.
    """

    def __init__(self, steps_per_revolution, rpm=10):
        self.steps_per_revolution = steps_per_revolution
        self.position = 0
        self.rpm = rpm

    @property
    def rpm(self):
        """Revolutions per minute. Ask for more than the motor can do and it just buzzes."""
        return self._rpm

    @rpm.setter
    def rpm(self, value):
        self._rpm = value
        self.step_delay_us = int(_MINUTE_US / (self.steps_per_revolution * value))

    @property
    def angle(self):
        """Where the shaft is, in degrees from where it started."""
        return self.position * 360 / self.steps_per_revolution

    @angle.setter
    def angle(self, degrees):
        self.move_to(round(degrees * self.steps_per_revolution / 360))

    def step(self, count):
        """Turns `count` steps, backwards if negative. Blocks until it has finished."""
        direction = 1 if count >= 0 else -1
        for _ in range(abs(count)):
            self._advance(direction)
            self.position += direction
            sleep_us(self.step_delay_us)

    def move_to(self, position):
        """Turns to a position in steps, by the shortest route there."""
        self.step(position - self.position)

    def _advance(self, direction):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError


class UnipolarStepper(Stepper):
    """Four coil pins, as on a ULN2003 board or an H bridge.

    `pins` are IN1 to IN4 in the order they are wired. A 28BYJ-48 has 2048 full steps or 4096
    half steps per revolution of its output shaft, gearing included.
    """

    def __init__(self, pins, steps_per_revolution=4096, rpm=10, sequence=HALF):
        self.pins = pins
        for pin in pins:
            pin.init(pin.OUT, value=0)
        self.sequence = sequence
        self._index = 0
        super().__init__(steps_per_revolution, rpm)

    def _advance(self, direction):
        self._index = (self._index + direction) % len(self.sequence)
        for pin, value in zip(self.pins, self.sequence[self._index]):
            pin.value(value)

    def release(self):
        """Turns the coils off.

        A stopped stepper is still holding, drawing its full current and getting warm, which is
        also what stops it being turned by hand. Releasing gives that up along with the holding
        torque, so anything the motor was supporting will move.
        """
        for pin in self.pins:
            pin.value(0)


class StepDirStepper(Stepper):
    """A step and direction driver: A4988, DRV8825, TMC2208 and the rest.

    A pulse on `step` moves one step, in whichever direction `direction` is set to. Microstepping
    is chosen with jumpers on the board rather than in software, so a driver set to sixteenth
    steps needs `steps_per_revolution` multiplied by 16.
    """

    def __init__(self, step, direction, enable=None, steps_per_revolution=200, rpm=60,
                 pulse_us=2, invert_enable=True):
        self._step = step
        self._direction = direction
        self._enable = enable
        self.pulse_us = pulse_us
        # Most of these boards enable when the pin is low, which is why it is inverted here.
        self._invert_enable = invert_enable
        step.init(step.OUT, value=0)
        direction.init(direction.OUT, value=0)
        if enable is not None:
            enable.init(enable.OUT, value=0 if invert_enable else 1)
        super().__init__(steps_per_revolution, rpm)

    def _advance(self, direction):
        self._direction.value(1 if direction > 0 else 0)
        self._step.value(1)
        sleep_us(self.pulse_us)
        self._step.value(0)

    def release(self):
        """Tells the driver board to let go, if its enable pin is wired."""
        if self._enable is not None:
            self._enable.value(1 if self._invert_enable else 0)
