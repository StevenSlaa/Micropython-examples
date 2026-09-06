from machine import Pin, SoftI2C
from time import sleep
from vcnl4040 import VCNL4040

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# subtracted from every proximity reading: set this to what proximity reads with nothing in
# front of the sensor, which is not zero once there is a window or a case in the way
cancellation = 0
# proximity count above which something counts as near, found by watching the numbers
near = 200

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = VCNL4040(i2c)
sensor.cancellation = cancellation

while True:
    proximity = sensor.proximity

    print(
        "Proximity: %5d  Light: %6.1f lux  White: %5d  %s"
        % (proximity, sensor.lux, sensor.white, "<- near" if proximity > near else "")
    )

    sleep(0.2)
