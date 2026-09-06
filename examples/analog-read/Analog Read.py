# Analog read: measuring a voltage, instead of only asking whether there is one.
#
# A digital pin gives you a yes or a no. This gives you a number, and that number is how a
# potentiometer, a light sensor, a soil moisture probe, a joystick and a battery monitor all
# work. Learn it once here and every one of those becomes the same three lines.

from machine import ADC, Pin
from time import sleep

# --- Configuration -------------------------------------------------------------------------
# Which pin to measure.
#
# On an ESP32, pick one from 32 to 39. Those belong to the converter called ADC1. The other
# analog pins are on ADC2, which quietly stops working the moment wifi is switched on — and
# finding that out by accident costs people an afternoon.
#
# On a Pico, use 26, 27 or 28.
adc_pin = 34

# What the board treats as a full scale reading. These boards run on 3.3V.
reference_volts = 3.3
# -------------------------------------------------------------------------------------------

adc = ADC(Pin(adc_pin))

# An ESP32 measures only a small part of the range unless you ask for more; this asks for the
# full 3.3V. A Pico has no such setting and does not recognise the word, which raises an error
# rather than doing nothing — so the try is what lets the same script run on both boards.
try:
    adc.atten(ADC.ATTN_11DB)
except AttributeError:
    pass

while True:
    # read_u16 always gives a number from 0 to 65535, on every board, however the hardware
    # underneath happens to work. That is the point of it: your code does not have to care.
    raw = adc.read_u16()

    # The raw number means nothing on its own. These two lines are what make it useful, and
    # they are the same arithmetic every time: divide by the biggest it can be, then multiply
    # by whatever you actually want to talk about.
    volts = raw / 65535 * reference_volts
    percent = raw / 65535 * 100

    print("Raw: %5d  Volts: %.2f  Percent: %.1f" % (raw, volts, percent))

    # Fast enough to feel responsive when you turn the knob, slow enough to read.
    sleep(0.2)
