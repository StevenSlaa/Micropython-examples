from machine import Pin
from time import sleep
from motor import Motor

# Configuration
# direction pins and the enable pin that carries the speed
in1_pin = 12
in2_pin = 14
enable_pin = 13
# set to None if your board's enable is jumpered high, as L298N modules ship. The PWM then
# goes on the direction pins instead, and both of those have to be PWM capable.
# enable_pin = None
# the fraction of full power below which this motor only hums instead of turning. Raise it
# until the slowest step below actually moves the shaft.
minimum = 0.3

motor = Motor(
    Pin(in1_pin),
    Pin(in2_pin),
    Pin(enable_pin) if enable_pin is not None else None,
    minimum=minimum,
)

while True:
    # Ramp up, so it is easy to see where this motor starts turning.
    for step in range(1, 11):
        speed = step / 10
        print("Speed: %.1f forward" % speed)
        motor.speed = speed
        sleep(0.4)

    print("Coasting")
    motor.speed = 0
    sleep(2)

    print("Speed: -0.6 backwards")
    motor.speed = -0.6
    sleep(2)

    # Braking shorts the motor's windings, which stops it far more sharply than coasting.
    print("Braking")
    motor.brake()
    sleep(2)
