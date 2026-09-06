from machine import Pin, SoftI2C
from time import sleep
from vl6180x import VL6180X, GAIN_1, RANGE_ERRORS

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# added to every reading in mm, to trim this particular sensor against a known distance
offset = 0

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = VL6180X(i2c, offset=offset)

while True:
    distance = sensor.range

    # The sensor answers with a number even when it saw nothing at all, so the status decides
    # whether that number means anything.
    if sensor.range_status == 0:
        print("Distance: %d mm  Light: %.0f lux" % (distance, sensor.lux(GAIN_1)))
    else:
        print("No reading:", RANGE_ERRORS.get(sensor.range_status, "unknown error"))

    sleep(0.5)
