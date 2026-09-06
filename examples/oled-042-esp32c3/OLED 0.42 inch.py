# The 0.42 inch OLED built into an ESP32-C3 SuperMini.
#
# The panel is 72x40 — 0.42 is the diagonal in inches, not a resolution — and it is driven by
# an SH1106, not the SSD1306 these modules are usually sold as. Both facts matter, and the
# README explains what each of them looks like when it is wrong.

from machine import Pin, SoftI2C
from time import sleep, ticks_ms
from sh1106 import SH1106_I2C, PANEL_72X40

# Configuration
# The display is wired to these two pins on this board. They are not the ones a plain
# SuperMini uses, so a pinout from elsewhere will not work here.
scl_pin = 6
sda_pin = 5

# 72x40, and PANEL_72X40 puts right the two settings the panel powers up with wrong: how many
# rows it has, and where those rows sit in the 64 the controller scans.
width = 72
height = 40

i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
display = SH1106_I2C(width, height, i2c, setup=PANEL_72X40)

# A border round the whole buffer is the quickest way to see that the geometry is right: all
# four edges should sit on the edges of the glass, with nothing clipped and no gap.
display.fill(0)
display.rect(0, 0, width, height, 1)
display.text("0.42in", 4, 6, 1)
display.text("72x40", 4, 18, 1)
display.show()
sleep(3)

# 40 pixels is five lines of the 8 pixel font, and 72 is nine characters. That is the whole
# canvas, so a small display is mostly an exercise in leaving things out.
started = ticks_ms()

while True:
    seconds = (ticks_ms() - started) // 1000

    display.fill(0)
    display.text("ESP32-C3", 0, 0, 1)
    display.text("SuperMini", 0, 10, 1)
    display.text("up %ds" % seconds, 0, 24, 1)
    # A line across the bottom, moving with the seconds, as something that visibly changes.
    display.hline(0, height - 1, min(seconds % 72, 72), 1)
    display.show()

    sleep(1)
