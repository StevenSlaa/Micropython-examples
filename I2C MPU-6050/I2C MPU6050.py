## Written by Steven Slaa
from machine import SoftI2C, Pin
from time import sleep
import mpu6050

i2c = SoftI2C(scl=Pin(9), sda=Pin(8))
mpu= mpu6050.accel(i2c)

while True:
 mpu.get_values()
 print(mpu.get_values())
 sleep(.1)
