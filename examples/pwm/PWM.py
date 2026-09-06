# Written by Steven Slaa

from machine import Pin, PWM
from time import sleep

# --- Configuration -------------------------------------------------------------------------
led_pin = 13

# How many times a second the pin is switched on and off. Below a few hundred you see it as
# flicker instead of brightness; 5000 is comfortably past that.
frequency = 5000

# How big a jump between brightness steps. The duty goes from 0 to 65535, so 256 gives 256
# steps, which is smooth to look at and quick enough to get through.
step = 256
# -------------------------------------------------------------------------------------------

led = PWM(Pin(led_pin))
led.freq(frequency)

while True:
    # Fade in: spend more and more of each cycle switched on.
    for duty in range(0, 65536, step):
        led.duty_u16(duty)
        # Printing every step would flood the console faster than it can be read, so this
        # prints roughly one line in eight. In the plotter it draws a triangle wave.
        if duty % (step * 8) == 0:
            print("Duty: %d" % duty)
        sleep(0.005)

    # And back out again.
    for duty in range(65535, -1, -step):
        led.duty_u16(duty)
        if duty % (step * 8) == 0:
            print("Duty: %d" % duty)
        sleep(0.005)
