from machine import Pin, SoftI2C
from time import sleep
from bh1750 import BH1750, CONTINUOUS_HIGH

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# 1 lux steps. Use CONTINUOUS_HIGH_2 for 0.5 lux steps in dim light (import it above)
mode = CONTINUOUS_HIGH
# measurement time, 31 to 254. 69 reads up to about 54 000 lux; use 31 in direct sunlight
mtreg = 69

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = BH1750(i2c, mode=mode, mtreg=mtreg)

while True:
    # a new reading takes 120ms at the default settings, so wait before reading the first one
    sleep(0.5)

    print(
        "Light: %8.1f lux  %s"
        % (sensor.lux, "<- saturated" if sensor.light == 65535 else "")
    )
