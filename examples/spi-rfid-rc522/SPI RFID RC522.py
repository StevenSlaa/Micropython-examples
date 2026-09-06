from time import sleep
from mfrc522 import MFRC522, uid_hex

# Configuration
# pins (SDA on the module is the SPI chip select)
sck_pin = 18
mosi_pin = 23
miso_pin = 19
rst_pin = 4
cs_pin = 5
# the block to read, and the factory key of a blank MIFARE Classic card
block = 8
key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

reader = MFRC522(sck=sck_pin, mosi=mosi_pin, miso=miso_pin, rst=rst_pin, cs=cs_pin)
print("Hold a card against the reader")

last = None

while True:
    serial = reader.scan()

    if not serial:
        # The card left the field, so the next time it comes back it is news again.
        last = None
        sleep(0.2)
        continue

    card = uid_hex(serial)

    if card != last:
        last = card
        print("Card:", card)

        if reader.select_tag(serial) == reader.OK:
            if reader.auth(reader.AUTHENT1A, block, key, serial) == reader.OK:
                data = reader.read(block)
                print("Block", block, "contains", bytes(data) if data else "nothing, the read failed")
            else:
                print("Could not authenticate; this card does not use the factory key")
            # Always close the session, or the next card will fail to authenticate.
            reader.stop_crypto1()

    sleep(0.2)
