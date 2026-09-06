# Written by Steven Slaa

from machine import Pin,PWM
from time import sleep

# According to the datasheet, servo has a pulse frequency of 50Hz
servo=PWM(Pin(17),freq=50)

# 50Hz means that one pulse is 20ms long
# The datasheet states the following:
# On time of 1ms 	= Full reverse (counterclockwise)
# On time of 1.5ms	= Stop rotation (stall)
# On time of 2ms	= Full forward (clockwise)
# With the following equation we can calculate the duty cycle that we need to send: OnTime(ms) / (1 / frequency(Hz))  * 1024

while True:
    # Full reverse
    servo.duty(51) # = 1ms / 20ms * 1024
    sleep(2)

    # Stop rotation
    servo.duty(77) # = 1.5ms / 20ms * 1024
    sleep(2)

    # Full forward
    servo.duty(102) # = 2ms / 20ms * 1024
    sleep(2)