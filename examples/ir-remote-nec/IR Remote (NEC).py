from machine import Pin
from time import sleep
from ir_receiver import IRReceiver

# Configuration
# pin the receiver's OUT leg is connected to
ir_pin = 15
# the onboard LED, toggled by one of the buttons below
led_pin = 2

# Buttons are only numbers until you write down which is which. Point your remote at the
# receiver, press every button, and fill in this table from what the console prints.
BUTTONS = {
    0x45: "power",
    0x46: "volume up",
    0x15: "volume down",
    0x40: "play",
}

led = Pin(led_pin, Pin.OUT)


def pressed(address, command, repeat):
    name = BUTTONS.get(command, "unknown")
    # No colon before these numbers on purpose: this is not a plottable reading, and the IDE
    # plotter would otherwise draw a meaningless series from it.
    print("Button %s (0x%02x) from address 0x%02x%s" % (name, command, address, " held" if repeat else ""))

    if name == "power" and not repeat:
        led.value(not led.value())


IRReceiver(Pin(ir_pin), pressed)

print("Point a remote at the receiver and press a button")

# The receiver runs from an interrupt, so the program is free to do anything else. This one
# just waits.
while True:
    sleep(1)
