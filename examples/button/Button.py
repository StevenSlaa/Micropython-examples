# Written by Steven Slaa

from machine import Pin
from time import sleep

# PULL_UP holds the pin at 3.3V through a resistor inside the chip, so the pin reads 1 while
# nothing is happening. The button's job is to connect the pin to GND, which reads 0.
# That is why a press reads 0 rather than 1, and why the button's other leg goes to GND.
button = Pin(12, Pin.IN, Pin.PULL_UP)
led = Pin(2, Pin.OUT)

while True:
    pressed = not button.value()

    if pressed:
        led.on()
    else:
        led.off()

    # Printing the state draws a square wave in the IDE plotter, which is a quick way to see
    # a switch bouncing. The short sleep keeps the console readable; without it the loop
    # prints thousands of lines a second.
    print("Pressed:", 1 if pressed else 0)
    sleep(0.05)
