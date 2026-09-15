from machine import ADC, Pin
from time import sleep
from mux74hc4051 import Mux74HC4051

# Configuration
# the select pins S0, S1 and S2
s0_pin = 16
s1_pin = 17
s2_pin = 18
# the enable pin E, or None if E is wired straight to GND
enable_pin = 19
# the common pin Z goes to an analog pin. On an ESP32 use 32 to 39, on a Pico 26, 27 or 28
adc_pin = 34
reference_volts = 3.3
# which channels to print. The plotter graphs four at most, so pick four to plot, e.g. (0, 1, 2, 3)
channels = range(8)

adc = ADC(Pin(adc_pin))
# an ESP32 only measures the full 3.3V with this; a Pico does not have the setting
try:
    adc.atten(ADC.ATTN_11DB)
except AttributeError:
    pass

mux = Mux74HC4051(
    Pin(s0_pin),
    Pin(s1_pin),
    Pin(s2_pin),
    enable=None if enable_pin is None else Pin(enable_pin),
    adc=adc,
)

while True:
    # read() switches to the channel, waits a moment for it to settle, then measures
    print("  ".join("Y%d: %.2f V" % (channel, mux.read(channel) / 65535 * reference_volts)
                    for channel in channels))
    sleep(0.5)
