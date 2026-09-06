# MQTT client (umqtt.simple)

The standard MicroPython MQTT client, published as a driver so the same code runs on every
board.

**ESP32 firmware already has this**, frozen in: `from umqtt.simple import MQTTClient` works
there with nothing installed. **A Raspberry Pi Pico W does not** — its firmware includes the
networking bundle but not umqtt — so the identical program fails at the import.

Installing this fills that gap. On an ESP32 the installed copy simply takes precedence over the
frozen one, which is harmless.

## Install

Install it from the Pulsar IoT library panel, or copy `umqtt/simple.py` to `/lib/umqtt/` on the
board, keeping the folder: it is a package, and `umqtt/simple.py` is the import path.

## Usage

```python
from umqtt.simple import MQTTClient

client = MQTTClient("my-board", "test.mosquitto.org", port=1883, keepalive=60)
client.connect()

client.publish(b"pulsar/temperature", b"21.5")

def arrived(topic, message):
    print(topic, message)

client.set_callback(arrived)
client.subscribe(b"pulsar/command")

while True:
    client.check_msg()      # returns straight away; wait_msg() blocks instead
```

## Notes

- Topics and payloads are `bytes`, not strings. `"text".encode()` on the way in and
  `.decode()` on the way out.
- `check_msg()` looks and returns; `wait_msg()` blocks until something arrives. A loop doing
  anything else wants `check_msg()`.
- `keepalive` matters. Set it, and call `ping()` or publish something within that many seconds,
  or the broker will drop you — silently, from your side.
- The client id must be unique on the broker. Two boards claiming the same one will disconnect
  each other in a loop, which looks like an unreliable network and is not.
- This is the simple client: it does not reconnect on its own. `umqtt.robust` adds that, and is
  in the same upstream repository.
- TLS needs `ssl_params` and is a good deal more memory than a small board has spare; plain 1883
  to a broker on your own network is the usual answer.

## Credits

From [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple),
MIT, vendored unchanged.

Used by: [mqtt](../../examples/mqtt)
