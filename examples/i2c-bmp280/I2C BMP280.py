# Written by Steven Slaa

import machine
from time import sleep
from bmp280 import *

sdaPIN=machine.Pin(8)  #for ESP32
sclPIN=machine.Pin(9)

i2c=machine.SoftI2C(sda=sdaPIN, scl=sclPIN, freq=10000)   

bmp = BMP280(i2c)

while True:
    # Both values on one line, and pressure in hectopascal so the two are closer in size:
    # the IDE plotter draws every series against one scale.
    print("Temperature: %.2f C  Pressure: %.1f hPa" % (bmp.temperature, bmp.pressure / 100))
    sleep(2)