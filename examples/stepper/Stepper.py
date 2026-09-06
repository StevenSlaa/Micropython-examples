from machine import Pin
from time import sleep
from stepper import UnipolarStepper, StepDirStepper, FULL, HALF

# Configuration
# "uln2003" for the little blue 28BYJ-48 motor and its driver board, or any stepper wired to
# four pins through an H bridge. "stepdir" for an A4988, DRV8825 or TMC2208 board.
wiring = "uln2003"

# uln2003: the four IN pins, in the order they are wired. If the motor hums and shakes instead
# of turning, swap the middle two.
coil_pins = (13, 12, 14, 27)

# stepdir: the step and direction pins, and the enable pin if you have wired it
step_pin = 13
direction_pin = 12
enable_pin = 14

# How many steps make one full turn of the output shaft. 4096 for a 28BYJ-48 half stepping,
# 2048 full stepping, 200 for most NEMA 17 motors before microstepping.
steps_per_revolution = 4096

# Revolutions per minute. A 28BYJ-48 runs out of puff at about 15; ask for more and it buzzes
# and stays put.
rpm = 10

if wiring == "uln2003":
    motor = UnipolarStepper(
        [Pin(pin) for pin in coil_pins],
        steps_per_revolution=steps_per_revolution,
        rpm=rpm,
        sequence=HALF,
    )
else:
    motor = StepDirStepper(
        Pin(step_pin),
        Pin(direction_pin),
        Pin(enable_pin),
        steps_per_revolution=steps_per_revolution,
        rpm=rpm,
    )

print("Steps per revolution:", steps_per_revolution)

while True:
    # A quarter turn at a time, so it is easy to check against something you can see. The
    # position is counted rather than measured: it is right only as long as nothing stops
    # the shaft.
    for angle in (90, 180, 270, 360):
        motor.angle = angle
        print("Angle: %.1f degrees" % motor.angle)

    # Straight back, the short way round, rather than continuing forwards.
    motor.move_to(0)
    print("Angle: %.1f degrees" % motor.angle)

    # Holding costs the same current as moving, and the motor gets warm doing it. Letting go
    # also lets the shaft be turned by hand, so try that while this pause runs.
    print("Released")
    motor.release()
    sleep(3)
