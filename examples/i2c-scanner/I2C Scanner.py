# Written by Steven Slaa

import machine

sdaPIN=machine.Pin(21)  #for ESP32
sclPIN=machine.Pin(22)

i2c=machine.SoftI2C(sda=sdaPIN, scl=sclPIN, freq=10000)   

devices = i2c.scan()
if len(devices) == 0:
 print("No I2C devices have been found!")
else:
 print('I2C devices found:',len(devices))
for device in devices:
 print("At address: ",hex(device))
