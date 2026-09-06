from machine import Pin, SoftI2C
from time import sleep
from eeprom import EEPROM

# Configuration
# pins
sda_pin = 21
scl_pin = 22
# the chip. "24LC01", "AT24C32", "CAT24C256" and the rest of the family are all understood.
part = "CAT24C256"
# where it answers on the bus: 0x50 with A0, A1 and A2 grounded, up to 0x57 with all three high
address = 0x50
# where in the chip to keep the boot counter. Byte 0 is as good as any.
counter_offset = 0

i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
memory = EEPROM.for_part(i2c, part, address)

print("Found a %s: %d bytes" % (part, len(memory)))

# --- A counter that survives being unplugged -------------------------------------------------
# This is what an EEPROM is for. RAM forgets the moment the power goes; this does not.

count = memory.read(counter_offset, 1)[0]
if count == 0xFF:
    # A new or erased chip reads as 0xff everywhere, which makes a useful "nothing here yet".
    print("This chip has never been written to")
    count = 0

count = (count + 1) % 255
memory.write(counter_offset, bytes([count]))
print("This board has now booted", count, "times")

# --- Writing and reading text ------------------------------------------------------------------
# An EEPROM stores bytes, not text, so a string is encoded on the way in and decoded coming out.

message = "Stored at %d boots" % count
memory.write(16, message.encode())
print("Wrote:", message)
print("Read back:", memory.read(16, len(message)).decode())

# --- Crossing a page boundary --------------------------------------------------------------
# These chips write in pages, and a write running off the end of one wraps back to its start
# instead of continuing. The driver splits writes so that cannot happen; this proves it, by
# writing a long run of bytes starting deliberately near the end of a page.

payload = bytes(range(200))
memory.write(60, payload)
print("200 bytes across page boundaries read back correctly:", memory.read(60, 200) == payload)

print("Reset the board to watch the counter go up")

while True:
    sleep(1)
