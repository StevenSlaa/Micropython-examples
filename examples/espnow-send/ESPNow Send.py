import network
import espnow
from time import sleep

# --- Configuration ---------------------------------------------------------------------------
# The receiving board prints its address when it starts; paste it here. The default is the
# broadcast address, which reaches every ESP-NOW board in range but never gets acknowledged.
receiver = b"\xff\xff\xff\xff\xff\xff"

# 1 to 13. Both boards must be on the same wifi channel.
channel = 1
# ---------------------------------------------------------------------------------------------

# ESP-NOW uses the wifi radio, so the station interface must be on. It does not connect anywhere.
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=channel)

esp = espnow.ESPNow()
esp.active(True)
esp.add_peer(receiver)

broadcast = receiver == b"\xff" * 6
print("Sending on channel", channel, "to", "everyone" if broadcast else receiver.hex(":"))

counter = 0
delivered = 0

while True:
    counter += 1
    # send() returns True when the other board's radio acknowledged the message. A broadcast is
    # never acknowledged, so there it only means the message left this board.
    if esp.send(receiver, str(counter)):
        delivered += 1
        print("Sent: %d  Delivered: %d  Lost: %d" % (counter, delivered, counter - delivered))
    else:
        print("Sent: %d  Delivered: %d  Lost: %d  (no answer)" % (counter, delivered, counter - delivered))
    sleep(1)
