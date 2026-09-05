# Written by Steven Slaa

import machine
from time import sleep
from bmp280 import *

sdaPIN=machine.Pin(8)  #for ESP32
sclPIN=machine.Pin(9)

i2c=machine.SoftI2C(sda=sdaPIN, scl=sclPIN, freq=10000)   

bmp = BMP280(i2c)

while True:
    print("Temperature: ",bmp.temperature, "°C")
    print("Pressure: ", bmp.pressure, "Pa")
    sleep(2)