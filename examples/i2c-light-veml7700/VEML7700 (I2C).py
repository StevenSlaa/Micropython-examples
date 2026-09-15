from machine import Pin, SoftI2C
from time import sleep
from veml7700 import VEML7700, GAIN_1_4, IT_100MS

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# the default reads a dark room up to about 17 000 lux. In sunlight use GAIN_1_8 and IT_25MS,
# and for very dim light GAIN_2 and IT_800MS (import them above)
gain = GAIN_1_4
integration_time = IT_100MS

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = VEML7700(i2c, gain=gain, integration_time=integration_time)

while True:
    # a new reading takes one integration time, so wait before reading the first one
    sleep(0.5)

    print(
        "Light: %8.1f lux  White: %5d  %s"
        % (sensor.lux, sensor.white, "<- saturated" if sensor.light == 65535 else "")
    )
