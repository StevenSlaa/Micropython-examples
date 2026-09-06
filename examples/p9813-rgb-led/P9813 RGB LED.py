from machine import Pin
from time import sleep
from p9813 import P9813

# Configuration
# pins
clock_pin = 14
data_pin = 13
# how many P9813 modules are chained
leds_count = 2
# 0.0 to 1.0. These are constant current drivers, so a chain at full brightness draws real power
brightness = 0.4

leds = P9813(clock=Pin(clock_pin), data=Pin(data_pin), n=leds_count, brightness=brightness)


def wheel(position):
    """A colour from around the wheel, 0 to 255, without needing any floating point maths."""
    position %= 256
    if position < 85:
        return (255 - position * 3, position * 3, 0)
    if position < 170:
        position -= 85
        return (0, 255 - position * 3, position * 3)
    position -= 170
    return (position * 3, 0, 255 - position * 3)


# The plain colours first, to check the wiring: a module showing green when it should be red has
# its channels swapped somewhere.
for name, colour in (("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255))):
    print("Showing", name)
    leds.fill(colour)
    leds.write()
    sleep(1)

print("Cycling")

step = 0
while True:
    # Spreading the wheel across the chain makes a rainbow that moves along it.
    for index in range(len(leds)):
        leds[index] = wheel(step + index * (256 // max(len(leds), 1)))
    leds.write()
    step += 2
    sleep(0.02)
