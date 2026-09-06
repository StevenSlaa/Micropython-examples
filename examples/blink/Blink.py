# Blink: the first program to run on any new board.
#
# Run this before anything else. If the light blinks, then your board works, your cable carries
# data (not every USB cable does), and MicroPython is installed and running. If it does not
# blink, the problem is one of those three things rather than anything you wrote, and every
# other experiment will be guesswork until this one works.

from machine import Pin
from time import sleep

# --- Configuration -------------------------------------------------------------------------
# Which pin the LED is on. 2 is the small onboard LED on most ESP32 boards, and 25 on a Pico.
# On a Pico W it is the text "LED" instead of a number, because that LED belongs to the wifi
# chip rather than to the main processor.
led_pin = 2

# How long the LED stays on, and then off, in seconds. 0.5 means one full blink per second.
interval = 0.5
# -------------------------------------------------------------------------------------------

# Pin.OUT tells the board that your program is in charge of this pin, and will decide what
# voltage it puts out. The other option, Pin.IN, means the opposite: the pin listens, and
# something else decides. A pin can only do one of the two at a time.
led = Pin(led_pin, Pin.OUT)

# while True means "keep doing this forever". Nearly every microcontroller program ends in one:
# there is no desktop to return to when it finishes, so it never finishes.
while True:
    # value(1) connects the pin to 3.3V. Current flows through the LED, and it lights.
    led.value(1)
    print("LED: 1")

    # Without this, the next line would run immediately and the LED would be on for a few
    # millionths of a second. It would still work; you just would not see it.
    sleep(interval)

    # value(0) connects the pin to 0V instead. No difference across the LED, so no light.
    led.value(0)
    print("LED: 0")

    sleep(interval)
