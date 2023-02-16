# Reference: https://microcontrollerslab.com/i2c-lcd-esp32-esp8266-micropython-tutorial/

import machine
from machine import Pin, SoftI2C
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from time import sleep

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)     #initializing the I2C method for ESP32

lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)

while True:
    lcd.move_to(2,0)
    lcd.putstr("MicroPython")
    lcd.move_to(0,1)
    lcd.putstr("I2C LCD Example")
    sleep(3)
    lcd.clear()
    lcd.move_to(1,0)
    lcd.putstr("Counter (0-10)")
    lcd.move_to(5,1)
    for i in range(11):
        lcd.move_to(7,1)
        lcd.putstr(str(i))
        sleep(1)
    lcd.clear()
    lcd.move_to(2,0)
    lcd.putstr("Created by")
    lcd.move_to(2,1)
    lcd.putstr("Steven Slaa")
    sleep(3)
    lcd.clear()
    