from machine import Pin, SPI
from struct import unpack
from sx127x import SX127x

# --- Pins: these suit a LilyGO T3 LoRa32 V1.6.1. The README lists other boards and modules. ----
spi_id = 1
sck_pin = 5
mosi_pin = 27
miso_pin = 19
cs_pin = 18
reset_pin = 23

# --- Radio: these must match the sending board exactly -----------------------------------------
# In Hz. 868MHz in Europe, 915MHz in the Americas and Australia, 433MHz for SX1278 boards.
frequency = 868_000_000

# 7 to 12. Higher reaches further, but every step up doubles the time each packet is on air.
spreading_factor = 9
bandwidth = 125_000
# ---------------------------------------------------------------------------------------------

spi = SPI(spi_id, baudrate=5_000_000, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
lora = SX127x(spi, cs=Pin(cs_pin), reset=Pin(reset_pin), frequency=frequency,
              bandwidth=bandwidth, spreading_factor=spreading_factor)

lora.receive()
print("Listening on", frequency / 1e6, "MHz")

expected = None
missed = 0

while True:
    packet = lora.recv()
    if packet is None:
        continue

    # Anything else on the same settings is heard too, so check this is the sender's four bytes.
    if len(packet) != 4:
        print("Other packet:", packet)
        continue
    counter = unpack("<I", packet)[0]

    # The counter goes up by one each time, so a gap means packets were lost on the way here.
    if expected is not None and counter > expected:
        missed += counter - expected
    expected = counter + 1

    # RSSI: -30 is next door, -120 is the edge. SNR: LoRa still decodes down to about -20 dB.
    print("RSSI: %d  SNR: %.1f  Missed: %d" % (lora.rssi, lora.snr, missed))
