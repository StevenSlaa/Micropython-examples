# Written by Steven Slaa

import time
from machine import Pin, SPI
import st7789py as st7789
import vga2_16x32 as font

# Configuration
# Fixed internal pins of the T-Display v1.1
lcd_sck = 18
lcd_mosi = 19
lcd_cs = 5
lcd_dc = 16
lcd_res = 23
lcd_bl = 4
button_left = 0
button_right = 35
# 1 or 3 is landscape (240x135), 0 or 2 is portrait (135x240)
rotation = 1

spi = SPI(1, baudrate=30000000, sck=Pin(lcd_sck), mosi=Pin(lcd_mosi))
display = st7789.ST7789(
    spi, 135, 240,
    reset=Pin(lcd_res, Pin.OUT),
    dc=Pin(lcd_dc, Pin.OUT),
    cs=Pin(lcd_cs, Pin.OUT),
    backlight=Pin(lcd_bl, Pin.OUT),
    rotation=rotation,
)
# Both buttons pull the pin low when pressed; GPIO 35 has an external pull-up on the board
btn_left = Pin(button_left, Pin.IN, Pin.PULL_UP)
btn_right = Pin(button_right, Pin.IN)

display.fill(st7789.BLACK)
display.text(font, "T-Display", 10, 5, st7789.RED)
display.text(font, "ST7789V", 10, 37, st7789.GREEN)

left = right = 0
last = None
while True:
    if not btn_left.value():
        left += 1
    if not btn_right.value():
        right += 1
    if (left, right) != last:
        last = (left, right)
        # Padded to a fixed width so the new text paints over the old one
        display.text(font, "L:{:<3} R:{:<3}".format(left % 1000, right % 1000), 10, 90, st7789.CYAN)
        print("Left:", left, "Right:", right)
    # ponytail: counts while held (~5/s), add edge detection if single presses matter
    time.sleep_ms(200)
