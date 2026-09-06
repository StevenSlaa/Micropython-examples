from machine import Pin, SPI
from time import sleep
from max7219 import Matrix8x8

# Configuration
# pins and bus: SPI 2 on an ESP32, SPI 0 on a Pico
spi_id = 2
sck_pin = 18
mosi_pin = 23
cs_pin = 5
# how many 8x8 modules are chained. A common 4-in-1 board is 4, giving 32x8 pixels
modules = 4
# 0 is dim and 15 is bright. Start low: a full chain at 15 draws more than a USB port gives
brightness = 2
# these boards are wired in more than one way, so if the display looks wrong, try these
reverse = False  # True if the text reads back to front
transpose = False  # True if the characters lie on their side
message = "MicroPython on a MAX7219 "

spi = SPI(spi_id, baudrate=10000000, polarity=1, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin))
display = Matrix8x8(spi, Pin(cs_pin), modules, reverse=reverse, transpose=transpose)
display.brightness(brightness)

# Something still first, so a wrong wiring option is easy to spot before anything moves.
display.fill(0)
display.text("Hi!", 0, 0, 1)
display.show()
sleep(2)

while True:
    # Drawing the whole message at a decreasing offset walks it across the chain. Anything
    # outside the display is simply not drawn, so no clipping is needed.
    for offset in range(len(message) * 8):
        display.fill(0)
        display.text(message, -offset, 0, 1)
        display.show()
        sleep(0.05)
