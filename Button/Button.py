from machine import Pin
import time

button = Pin(12, Pin.IN, Pin.PULL_UP)
led = Pin(2, Pin.OUT)

while True :
    if button.value():
        led.on()
    else:
        led.off()