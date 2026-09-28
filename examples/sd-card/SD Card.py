from machine import Pin
from time import ticks_ms
import os

# --- Pins: these suit a LilyGO T3 LoRa32 V1.6.1. The README lists other boards and modules. ----
sck_pin = 14
mosi_pin = 15
miso_pin = 2
cs_pin = 13
# ---------------------------------------------------------------------------------------------

try:
    # ESP32 firmware has SD card support built in, so no driver is needed. Slot 2 talks to the
    # card over SPI; use 3 if something else in your script already has SPI(1), such as a radio.
    from machine import SDCard
    sd = SDCard(slot=2, sck=sck_pin, mosi=mosi_pin, miso=miso_pin, cs=cs_pin)
except ImportError:
    # Other boards, like the Pico, use micropython-lib's driver. Install it once from the REPL
    # with: import mip; mip.install("sdcard")
    from machine import SPI
    from sdcard import SDCard
    sd = SDCard(SPI(0, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin)), Pin(cs_pin))

# From here on the card is a folder, and files on it work like any other file.
os.mount(sd, "/sd")

stats = os.statvfs("/sd")
block = stats[0]
print("Size: %d MB  Free: %d MB" % (stats[2] * block // 1_000_000, stats[3] * block // 1_000_000))

# "a" adds to the end, so every run leaves one more line behind, even after the power is cut.
with open("/sd/log.txt", "a") as f:
    f.write("Started, %d ms after boot\n" % ticks_ms())

print("log.txt now holds:")
with open("/sd/log.txt") as f:
    print(f.read())

print("Files on the card:", os.listdir("/sd"))

# Unmount before pulling the card out, or the last writes may never reach it.
os.umount("/sd")
