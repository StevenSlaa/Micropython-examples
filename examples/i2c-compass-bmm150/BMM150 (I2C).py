from machine import Pin, SoftI2C
from time import sleep
from bmm150 import BMM150, REGULAR, RATE_10HZ

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# 0x10 to 0x13 depending on the breakout. If it is not found, run an I2C scan
address = 0x10
# LOW_POWER, REGULAR, ENHANCED or HIGH_ACCURACY (import it above). More accurate is slower
preset = REGULAR
rate = RATE_10HZ
# your local magnetic declination in degrees, east positive, or 0 for magnetic north
declination = 0
# set to True once to work out the correction for your module, then paste the result below
calibrating = False
offset = (0.0, 0.0, 0.0)
scale = (1.0, 1.0, 1.0)

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = BMM150(i2c, address=address, preset=preset, rate=rate, offset=offset, scale=scale)

# the first sample takes one measurement to arrive; before that every axis reads nan
sleep(0.2)

if calibrating:
    print("Turn the module slowly through every orientation for 20 seconds...")
    measured_offset, measured_scale = sensor.calibrate(seconds=20)
    print("offset =", measured_offset)
    print("scale =", measured_scale)
    print("Paste those into this script and set calibrating back to False")

while True:
    x, y, z = sensor.magnetic
    # an axis that went out of range is nan, and nan is the only value not equal to itself
    if x != x or y != y or z != z:
        print("Out of range  <- overflow, is there a magnet nearby?")
    else:
        print(
            "X: %.1f uT  Y: %.1f uT  Z: %.1f uT  Heading: %.0f degrees"
            % (x, y, z, sensor.heading(declination))
        )
    sleep(0.5)
