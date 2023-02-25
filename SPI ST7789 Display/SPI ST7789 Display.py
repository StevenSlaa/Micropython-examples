# Written by Steven Slaa

import uos
import machine
import st7789py as st7789
import vga2_16x32 as font

# Configuration
# pins
st7789_res = 14
st7789_dc  = 12
# display
disp_width = 240
disp_height = 240
# utils
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)

pin_st7789_res = machine.Pin(st7789_res, machine.Pin.OUT)
pin_st7789_dc = machine.Pin(st7789_dc, machine.Pin.OUT)
spi2 = machine.SPI(2, baudrate=40000000, polarity=1)

# Print basic information
print(uos.uname())
print(spi2)

# Initialize display
display = st7789.ST7789(spi2, disp_width, disp_width, reset=pin_st7789_res, dc=pin_st7789_dc, rotation=0)

display.fill(st7789.BLACK)
display.text(font, "SPI ST7789", 10, 10, color=0xF800)
display.text(font, "Display", 10, 40, color=0x07E0)
display.text(font, "Example", 10, 70, color=0x001F)
display.text(font, "Created by:", 10, 170)
display.text(font, "Steven Slaa", 10, 200, color=0xFFFF)
