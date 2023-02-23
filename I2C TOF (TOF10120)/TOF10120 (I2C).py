import machine
from time import sleep

sdaPIN=machine.Pin(8)  #for ESP32
sclPIN=machine.Pin(9)

i2c=machine.SoftI2C(sda=sdaPIN, scl=sclPIN, freq=10000)   
       
addr = i2c.scan()[0]
data = bytearray(2)

while True:
    i2c.readfrom_mem_into(addr, 0, data)
    distance = data[0] << 8 | data[1]
    print(distance)
    sleep(.1)