from machine import Pin, SoftI2C
from time import sleep
from ds3231 import DS3231

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# Set this once to put the time on the module, then set it back to None and run again. The
# coin cell keeps it running from then on, through resets and power cuts.
# (year, month, day, hour, minute, second, weekday) with weekday 0 for Monday
set_time = None
# set_time = (2026, 9, 6, 14, 32, 0, 6)

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
clock = DS3231(i2c)

if set_time:
    clock.datetime = set_time
    print("Clock set")

if clock.lost_power:
    # The chip says its oscillator has stopped, so whatever it reads is not a real time. This
    # is what a module that has never been set, or one with a flat battery, looks like.
    print("The clock is not set. Put a time in set_time at the top of this script and run it.")
else:
    # Hand the time to the board, so time.localtime() and anything using it are correct too.
    clock.sync_board()
    print("Board clock set from the module")

while True:
    year, month, day, hour, minute, second, weekday = clock.datetime

    # The date has no letters in it, so the IDE plotter reads only the temperature from this
    # line and graphs that.
    print(
        "%04d-%02d-%02d %02d:%02d:%02d  Temperature: %.2f C"
        % (year, month, day, hour, minute, second, clock.temperature)
    )

    sleep(1)
