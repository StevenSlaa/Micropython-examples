from time import sleep
from hx711 import HX711

# Configuration
# pins
dout_pin = 16
sck_pin = 17
# the weight you calibrate with, in grams. Anything you know the weight of works: a bag of sugar,
# a full 500 ml water bottle (about 520 g), a phone checked on a kitchen scale
calibration_weight = 500
# raw counts per gram. Leave at None to calibrate on start, then paste the printed value here
scale = None
# readings averaged for each line printed. More is steadier and slower (about 10 per second)
samples = 5
# grams either side of zero shown as 0, to hide noise on an empty scale. Raise it for big load cells
zero_band = 0.5

sensor = HX711(dout_pin, sck_pin)

print("Taring: keep the scale empty")
sleep(1)
sensor.tare()

if scale is None:
    print("Place %d g on the scale, measuring in 10 seconds" % calibration_weight)
    sleep(10)
    scale = sensor.calibrate(calibration_weight)
    print("Calibrated: set  scale = %.2f  at the top to skip this next time" % scale)
else:
    sensor.scale = scale

while True:
    grams = sensor.weight(samples)
    if abs(grams) < zero_band:
        grams = 0
    print("Weight: %8.1f g" % grams)
