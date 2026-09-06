from machine import Pin, SPI
from time import sleep, ticks_ms
from struct import pack
from nrf24l01 import NRF24L01

# --- Configuration: this block must match the receiving board exactly --------------------------
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

# Five byte addresses. They are names, not routes: this board sends to the first and would
# listen for replies on the second. The receiving board has them the other way round.
send_to = b"\xe1\xf0\xf0\xf0\xf0"
reply_to = b"\xd2\xf0\xf0\xf0\xf0"
# ---------------------------------------------------------------------------------------------

spi = SPI(spi_id, sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=Pin(miso_pin))
radio = NRF24L01(spi, Pin(csn_pin), Pin(ce_pin), channel=channel, payload_size=payload_size)

radio.open_tx_pipe(send_to)
radio.open_rx_pipe(1, reply_to)
# A module cannot listen and transmit at once.
radio.stop_listening()

print("Sending on channel", channel)

counter = 0
delivered = 0

while True:
    counter += 1

    try:
        # The receiving module acknowledges in hardware, so this returning means the packet
        # genuinely arrived. The chip has already retried eight times before giving up.
        radio.send(pack("<ii", counter, ticks_ms()))
        delivered += 1
        print("Sent: %d  Delivered: %d  Lost: %d" % (counter, delivered, counter - delivered))
    except OSError:
        # Nothing acknowledged: the other board is off, out of range, on another channel, or
        # its supply is dipping when it tries to answer.
        print("Sent: %d  Delivered: %d  Lost: %d  (no answer)" % (counter, delivered, counter - delivered))

    sleep(1)
