# Publishing readings to an MQTT broker and listening for commands, which is how most small
# devices actually get their data anywhere.
#
# MQTT is a post office rather than a phone call. Nothing connects to this board: it publishes
# to a named topic on a broker, and anything that cares subscribes to that topic. The two never
# have to be running at the same moment, or know about each other at all.

from time import sleep, ticks_diff, ticks_ms
from umqtt.simple import MQTTClient
import wifi

# --- Configuration ---------------------------------------------------------------------------
SSID = "your-network"
PASSWORD = "your-password"

# A public broker, handy for trying this out. Anything you publish here is visible to the whole
# internet, so use your own broker for anything real: Mosquitto on a Raspberry Pi is ten
# minutes of work.
broker = "test.mosquitto.org"
port = 1883

# Must be unique on the broker. Two boards claiming the same name disconnect each other in a
# loop, which looks exactly like a bad network.
client_id = "pulsar-example-board"

# Topics are just names, and the slashes mean nothing to the broker. Change this prefix to
# something of your own, or you will be reading somebody else's readings on a public broker.
prefix = "pulsar/example"
readings_topic = ("%s/readings" % prefix).encode()
command_topic = ("%s/command" % prefix).encode()

# seconds between readings. Also see keepalive below.
interval = 5
# ----------------------------------------------------------------------------------------------

station = wifi.connect(SSID, PASSWORD)
print("Connected as", wifi.address(station))

# keepalive is a promise: say something at least this often, or the broker will decide the
# board has gone. The loop below publishes well inside it.
client = MQTTClient(client_id, broker, port=port, keepalive=60)


def arrived(topic, message):
    # Runs from inside check_msg(), so it should be quick and must not raise.
    print("Command: %s -> %s" % (topic.decode(), message.decode()))


client.set_callback(arrived)
client.connect()
client.subscribe(command_topic)

print("Publishing to", readings_topic.decode())
print("Listening on", command_topic.decode())

reading = 0
last_published = ticks_ms()

while True:
    # Topics and payloads are bytes, not strings, all the way through MQTT.
    client.check_msg()  # returns at once; wait_msg() would block until something arrived

    if ticks_diff(ticks_ms(), last_published) >= interval * 1000:
        last_published = ticks_ms()
        reading += 1
        # A real one would be a sensor. Anything from the Sensors examples drops straight in.
        payload = b"%d" % reading
        client.publish(readings_topic, payload)
        print("Published: %d" % reading)

    sleep(0.1)
