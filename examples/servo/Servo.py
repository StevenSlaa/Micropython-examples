from machine import Pin
from time import sleep
from servo import Servo

# Configuration
# the pin the servo's signal wire is on. Its power must come from somewhere other than the
# board's 3.3V pin: even a small servo browns the board out when it starts moving.
servo_pin = 17

# False for the usual servo, which turns to an angle and holds it.
# True for a 360 degree servo, which turns continuously and takes a speed instead.
continuous = False

# The pulse lengths at the ends of the travel, in microseconds. Measure these once for your
# servo: see "Tuning it" in the README. A continuous servo wants the narrower 1000 to 2000.
min_us = 1000 if continuous else 500
max_us = 2000 if continuous else 2500

# Where a continuous servo stands still. Trim it if yours creeps when told to stop.
stop_us = 1500

servo = Servo(Pin(servo_pin), min_us=min_us, max_us=max_us, stop_us=stop_us)

if continuous:
    while True:
        # A continuous servo reads the pulse as a speed and a direction.
        for speed, name in ((1.0, "full speed"), (0.35, "slowly"), (0, "stopped"),
                            (-0.35, "slowly back"), (-1.0, "full speed back")):
            print("Speed: %.2f  (%s)" % (speed, name))
            servo.speed = speed
            sleep(2)

        # Releasing is not the same as a speed of zero: the servo stops being driven at all and
        # coasts, instead of actively holding itself still.
        print("Released")
        servo.release()
        sleep(2)
else:
    while True:
        # A positional servo turns to an angle and holds it there.
        for angle in (0, 90, 180, 90):
            print("Angle: %d degrees" % angle)
            servo.angle = angle
            # Servos are not instant. This is long enough for a small one to cross its travel.
            sleep(1)

        # Sweeping, rather than jumping between positions.
        for angle in range(0, 181, 5):
            servo.angle = angle
            print("Angle: %d degrees" % angle)
            sleep(0.02)

        # A released servo goes limp: it stops buzzing, stops drawing current, and can be turned
        # by hand.
        print("Released")
        servo.release()
        sleep(2)
