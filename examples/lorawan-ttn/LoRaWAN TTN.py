from machine import Pin, SPI
from time import sleep
from struct import pack
from binascii import hexlify
from sx127x import SX127x
from lorawan import LoRaWAN

# --- Pins: these suit a LilyGO T3 LoRa32 V1.6.1. The README lists other boards and modules. ----
spi_id = 1
sck_pin = 5
mosi_pin = 27
miso_pin = 19
cs_pin = 18
reset_pin = 23

# --- The Things Network: copy these from the device's page in the console, as shown there ------
dev_eui = "0000000000000000"
join_eui = "0000000000000000"
app_key = "00000000000000000000000000000000"

# The frequency plan picked when registering the device: EU868, US915 or AU915.
region = "EU868"

# 7 to 12 in Europe, 7 to 10 in the US and Australia. Higher reaches a gateway further away, but
# every step up doubles the airtime.
spreading_factor = 9

# dBm. 14 is the legal limit on the European channels; up to 20 is allowed in the US and Australia.
tx_power = 14

# Seconds between uplinks. TTN allows each device 30 seconds on air a day, which at spreading
# factor 9 is one small uplink about every ten minutes.
interval = 600
# ---------------------------------------------------------------------------------------------

if app_key.strip("0") == "":
    raise SystemExit("Fill in dev_eui, join_eui and app_key from the TTN console first")

spi = SPI(spi_id, baudrate=5_000_000, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
lora = SX127x(spi, cs=Pin(cs_pin), reset=Pin(reset_pin), tx_power=tx_power)
ttn = LoRaWAN(lora, dev_eui, join_eui, app_key, region=region, spreading_factor=spreading_factor)

# The session is kept in flash, so after a reset this is skipped and the device carries on.
attempt = 0
while not ttn.joined:
    attempt += 1
    print("Joining, attempt", attempt)
    if not ttn.join():
        # Usually no gateway in range, or a key copied wrongly. Wait longer each time, so a device
        # out of range does not fill the air with requests.
        print("No answer from the network")
        sleep(min(30 * attempt, 600))

print("Joined, device address", hexlify(ttn.dev_addr[::-1]).decode().upper())

counter = 0

while True:
    counter += 1

    # Two bytes, most significant first. The README has the formatter that turns them back into a
    # number in the console.
    reply = ttn.send(pack(">H", counter & 0xFFFF), port=1)
    print("Sent: %d  Frame: %d" % (counter, ttn.fcnt_up - 1))

    # Downlinks queued in the console arrive in the few seconds after an uplink, and only then.
    if reply:
        print("Downlink:", reply)

    sleep(interval)
