# Reading a knob and dimming an LED with it: an input and an output, joined together.
#
# The wiring here is just the two previous examples at once. The part worth your attention is
# the two lines in the middle, because joining any input to any output is the same problem, and
# this is the shape of the answer.

from machine import ADC, PWM, Pin
from time import sleep

# --- Configuration -------------------------------------------------------------------------
# The knob. On an ESP32 use 32 to 39; on a Pico use 26, 27 or 28.
adc_pin = 34

# The LED. Nearly any pin can do this.
led_pin = 2

# How many times a second the LED is switched on and off to fake a brightness. Anything above
# a few hundred is too fast to see, and 1000 is a comfortable choice.
frequency = 1000
# -------------------------------------------------------------------------------------------

adc = ADC(Pin(adc_pin))
try:
    adc.atten(ADC.ATTN_11DB)  # ESP32: measure the whole 3.3V. A Pico has no such setting.
except AttributeError:
    pass

led = PWM(Pin(led_pin))
led.freq(frequency)

while True:
    raw = adc.read_u16()  # 0 to 65535, wherever the knob is

    # Step one: turn the reading into a fraction of the way along, from 0.0 to 1.0.
    #
    # Do this first, always, whatever the input is. A knob gives 0 to 65535; a temperature
    # might give -40 to 125; a distance sensor gives millimetres. Once each of them is a plain
    # fraction, they all behave the same, and the rest of your program stops caring which
    # sensor it came from.
    fraction = raw / 65535

    # Step two: stretch that fraction to whatever the output needs.
    #
    # Here the LED also wants 0 to 65535, so this line looks like it is doing nothing at all.
    # Write it anyway. When the output becomes a servo that wants 40 to 115, or a volume that
    # wants 0 to 30, this is the only line that changes:
    #
    #     angle  = int(40 + fraction * (115 - 40))
    #     volume = int(fraction * 30)
    #
    duty = int(fraction * 65535)
    led.duty_u16(duty)

    print("Raw: %5d  Brightness: %.1f" % (raw, fraction * 100))
    sleep(0.05)
