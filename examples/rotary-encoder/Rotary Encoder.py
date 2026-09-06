from machine import Pin
from time import sleep
from rotary import RotaryEncoder

# Configuration
# pins
clk_pin = 13
dt_pin = 12
sw_pin = 14
# the range the value is kept inside
minimum = 0
maximum = 100
# True if turning it clockwise makes the number go down
reverse = False
# how many electrical steps your encoder makes per notch you can feel. Four is much the most
# common; try 1 or 2 if one click moves the value by more than one.
steps_per_detent = 4

knob = RotaryEncoder(
    clk=Pin(clk_pin),
    dt=Pin(dt_pin),
    sw=Pin(sw_pin),
    value=50,
    minimum=minimum,
    maximum=maximum,
    reverse=reverse,
    steps_per_detent=steps_per_detent,
)

print("Turn the knob, and press it to reset to 50")

# Turning is handled by interrupts, so this loop does not have to be quick to keep up. It only
# has to notice when something changed.
last = None

while True:
    if knob.was_pressed():
        knob.value = 50
        print("Reset")

    # Printing only on a change, rather than the same number twenty times a second.
    if knob.value != last:
        last = knob.value
        # A bar as well as the number, because a knob is easier to judge by eye.
        print("Value: %3d  %s" % (last, "#" * (last // 5)))

    sleep(0.05)
