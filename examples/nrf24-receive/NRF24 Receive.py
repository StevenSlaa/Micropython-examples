from machine import Pin, SPI
from time import ticks_diff, ticks_ms
from struct import unpack
from nrf24l01 import NRF24L01

# --- Configuration: this block must match the sending board exactly ---------------------------
# pins. spi_id 2 with these pins suits an ESP32; a Pico wants 0, sck 2, mosi 3, miso 4.
spi_id = 2
sck_pin = 18
mosi_pin = 23
miso_pin = 19
csn_pin = 5
ce_pin = 4

# 0 to 125. Above 76 is usually quieter, because wifi crowds the bottom of the band.
channel = 76

# bytes per packet, up to 32. Both ends must agree, or the data arrives as rubbish.
payload_size = 8

# The same two addresses as the sender, the other way round: this board listens on the one the
# sender sends to.
listen_on = b"\xe1\xf0\xf0\xf0\xf0"
reply_to = b"\xd2\xf0\xf0\xf0\xf0"
# ---------------------------------------------------------------------------------------------

spi = SPI(spi_id, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
radio = NRF24L01(spi, Pin(csn_pin), Pin(ce_pin), channel=channel, payload_size=payload_size)

radio.open_tx_pipe(reply_to)
radio.open_rx_pipe(1, listen_on)
radio.start_listening()

print("Listening on channel", channel)

expected = None
missed = 0

while True:
    if not radio.any():
        continue

    packet = radio.recv()
    # The sender packed two 32 bit integers; the rest of the packet is padding.
    counter, sent_at = unpack("<ii", packet[:8])

    # The counter goes up by one each time, so a gap means packets were lost on the way here.
    # The sender cannot see these: it was told they were acknowledged.
    if expected is not None and counter != expected:
        missed += counter - expected
    expected = counter + 1

    print("Counter: %d  Missed: %d" % (counter, missed))
