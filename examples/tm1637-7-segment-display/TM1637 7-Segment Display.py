from machine import Pin
from time import localtime, sleep
import tm1637

# Configuration
# pins: any two GPIOs. This is not I2C, so it cannot share a bus with I2C devices
clk_pin = 14
dio_pin = 12
# 0 is dimmest and 7 brightest
brightness = 5

display = tm1637.TM1637(clk=Pin(clk_pin), dio=Pin(dio_pin), brightness=brightness)

# A few of the things the display can do, before the clock starts.
display.show("boot")
sleep(1)
display.number(1234)
sleep(1)
display.scroll("hello ", delay=200)

# Minutes and seconds from the board's own clock, with the colon blinking once a second.
# Nothing has set that clock, so this counts from whenever the board was powered up rather
# than telling the actual time: for that the board needs the network or an RTC module.
while True:
    now = localtime()
    minutes = now[4]
    seconds = now[5]

    display.numbers(minutes, seconds, colon=True)
    sleep(0.5)
    display.numbers(minutes, seconds, colon=False)
    sleep(0.5)
