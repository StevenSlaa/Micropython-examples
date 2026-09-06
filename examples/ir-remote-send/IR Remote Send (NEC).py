from machine import Pin
from time import sleep
from ir_transmitter import IRTransmitter

# Configuration
# pin driving the IR LED, through a resistor or a transistor
ir_pin = 4
# the codes to send, as an IR receiver reports them: (address, command, name)
CODES = (
    (0x00, 0x45, "power"),
    (0x00, 0x46, "volume up"),
    (0x00, 0x15, "volume down"),
)
# how many extra "same again" frames to send, as if the button were held. Two is worth using
# on a board without RMT, where the occasional frame can be spoiled by an interrupt.
repeats = 0

transmitter = IRTransmitter(Pin(ir_pin))

# rmt on an ESP32, where the carrier comes out of hardware, and pwm anywhere else.
print("Sending with the", transmitter.backend, "backend")

while True:
    for address, command, name in CODES:
        print("Sent %s (0x%02x) to address 0x%02x" % (name, command, address))
        transmitter.send(address, command, repeats=repeats)
        sleep(2)
