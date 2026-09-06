from machine import Pin
from keypad import Keypad

# Configuration
# the four row pins and the four column pins, in the order they are wired
row_pins = (13, 12, 14, 27)
column_pins = (26, 25, 33, 32)
# the code to unlock, typed then confirmed with #. * clears what has been typed so far
secret = "1234"

pad = Keypad([Pin(pin) for pin in row_pins], [Pin(pin) for pin in column_pins])

typed = ""
print("Type a code and press # to check it, or * to clear")

while True:
    # read() reports each press once, however long the key is held, and does its own
    # debouncing, so the loop needs no sleep of its own.
    key = pad.read()
    if not key:
        continue

    if key == "*":
        typed = ""
        print("Cleared")
    elif key == "#":
        print("Unlocked" if typed == secret else "Wrong code")
        typed = ""
    else:
        typed += key
        # Printing stars rather than the digits, since this is a code being entered.
        print("Entered", "*" * len(typed))
