from machine import Pin, SoftI2C
from time import sleep
from qmc5883l import QMC5883L, RANGE_8G

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# RANGE_2G has finer steps but overflows near magnets; RANGE_8G is the safe default
field_range = RANGE_8G
# your local magnetic declination in degrees, east positive, or 0 for magnetic north
declination = 0
# set to True once to work out the correction for your module, then paste the result below
calibrating = False
offset = (0.0, 0.0, 0.0)
scale = (1.0, 1.0, 1.0)

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
sensor = QMC5883L(i2c, field_range=field_range, offset=offset, scale=scale)

if calibrating:
    print("Turn the module slowly through every orientation for 20 seconds...")
    measured_offset, measured_scale = sensor.calibrate(seconds=20)
    print("offset =", measured_offset)
    print("scale =", measured_scale)
    print("Paste those into this script and set calibrating back to False")

while True:
    x, y, z = sensor.magnetic
    print(
        "X: %.1f uT  Y: %.1f uT  Z: %.1f uT  Heading: %.0f degrees  %s"
        % (x, y, z, sensor.heading(declination), "<- overflow" if sensor.overflow else "")
    )
    sleep(0.5)
