## Written by Steven Slaa
from machine import SoftI2C, Pin
from time import sleep
import mpu6050

i2c = SoftI2C(scl=Pin(9), sda=Pin(8))
mpu= mpu6050.accel(i2c)

while True:
 values = mpu.get_values()
 # Printing the dictionary straight out gives Python's own format, which the IDE plotter
 # cannot read. Naming each value plots it, three axes of the same size against each other.
 # Swap AcX/AcY/AcZ for GyX/GyY/GyZ to watch the gyroscope, or Tmp for the temperature.
 print('AcX: %d  AcY: %d  AcZ: %d' % (values['AcX'], values['AcY'], values['AcZ']))
 sleep(.1)
