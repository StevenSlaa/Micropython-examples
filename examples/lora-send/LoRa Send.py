from machine import Pin, SPI
from time import sleep_ms, ticks_diff, ticks_ms
from struct import pack
from sx127x import SX127x

# --- Pins: these suit a LilyGO T3 LoRa32 V1.6.1. The README lists other boards and modules. ----
spi_id = 1
sck_pin = 5
mosi_pin = 27
miso_pin = 19
cs_pin = 18
reset_pin = 23

# --- Radio: these must match the receiving board exactly ---------------------------------------
# In Hz. 868MHz in Europe, 915MHz in the Americas and Australia, 433MHz for SX1278 boards: use the
# band your radio was sold for, because its antenna is tuned to it.
frequency = 868_000_000

# 7 to 12. Higher reaches further, but every step up doubles the time each packet is on air.
spreading_factor = 9
bandwidth = 125_000

# 2 to 20 dBm. Only this end cares; the receiver does not have to match it.
tx_power = 17
# ---------------------------------------------------------------------------------------------

spi = SPI(spi_id, baudrate=5_000_000, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
lora = SX127x(spi, cs=Pin(cs_pin), reset=Pin(reset_pin), frequency=frequency,
              bandwidth=bandwidth, spreading_factor=spreading_factor, tx_power=tx_power)

print("Sending on", frequency / 1e6, "MHz")

counter = 0

while True:
    counter += 1

    start = ticks_ms()
    # Four bytes: the counter. The receiver uses the gaps between counters to spot lost packets,
    # because LoRa itself never tells the sender whether anything arrived.
    lora.send(pack("<I", counter))
    airtime = ticks_diff(ticks_ms(), start)

    print("Sent: %d  Airtime: %d ms" % (counter, airtime))

    # Europe's 868MHz band allows 1% of the time on air, so wait 99 times as long as sending
    # took. Never less than a second, so the output stays readable.
    sleep_ms(max(1000, airtime * 99))
