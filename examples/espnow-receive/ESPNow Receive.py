import network
import espnow

# --- Configuration ---------------------------------------------------------------------------
# 1 to 13. Both boards must be on the same wifi channel.
channel = 1
# ---------------------------------------------------------------------------------------------

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=channel)

esp = espnow.ESPNow()
esp.active(True)

# Copy this into the sending board's `receiver` setting.
mac = sta.config("mac")
print("My address:", mac.hex(":"))
print('Sender setting: receiver = b"' + "".join("\\x%02x" % b for b in mac) + '"')
print("Listening on channel", channel)

expected = None
missed = 0

while True:
    # Waits until a message arrives; no peer has to be added just to receive.
    sender, msg = esp.recv()
    if msg is None:
        continue

    counter = int(msg)
    # The counter goes up by one each time, so a gap means messages were lost on the way here.
    if expected is not None and counter > expected:
        missed += counter - expected
    expected = counter + 1

    print("From: %s  Counter: %d  Missed: %d" % (sender.hex(":"), counter, missed))
