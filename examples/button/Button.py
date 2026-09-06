# Written by Steven Slaa

from machine import Pin
from time import sleep

button = Pin(12, Pin.IN, Pin.PULL_UP)
led = Pin(2, Pin.OUT)

while True :
    if button.value():
        led.on()
    else:
        led.off()
    # Printing the state draws a square wave in the IDE plotter, which is a quick way to see
    # a switch bouncing. The short sleep keeps the console readable; without it the loop
    # prints thousands of lines a second.
    print("Button:", button.value())
    sleep(0.05)