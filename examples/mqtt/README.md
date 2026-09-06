---
example: mqtt
author: Steven Slaa
---

# 5. MQTT

Publishes a reading every few seconds to an MQTT broker, and listens for commands coming back.

This is how most small devices actually send their data anywhere. MQTT is a post office rather
than a phone call: nothing connects to your board. It publishes to a named topic on a broker,
and whatever cares subscribes to that topic. The two never have to be running at the same
moment, or know anything about each other.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Wifi and access points](../../drivers/wifi) and
[MQTT client (umqtt.simple)](../../drivers/umqtt) drivers installed on the board.
> Install them from the library panel in the Pulsar IoT IDE, or copy the drivers' `.py`
> files into `/lib` on the microcontroller yourself.

The MQTT client is included in ESP32 firmware already, but **not** in the Pico W's. Installing
it means the same script runs on both, which is the whole reason it is in the catalog.

## Run it

Put your network details and a topic prefix of your own at the top, then:

```
Connected as 192.168.1.50
Publishing to pulsar/example/readings
Listening on pulsar/example/command
Published: 1
Published: 2
Command: pulsar/example/command -> hello
```

To watch it from a computer, with Mosquitto's tools installed:

```sh
mosquitto_sub -h test.mosquitto.org -t 'pulsar/example/readings' -v
mosquitto_pub -h test.mosquitto.org -t 'pulsar/example/command' -m hello
```

The first prints every reading as it arrives. The second sends a command, which appears on the
board within a fraction of a second.

## The public broker

`test.mosquitto.org` is open to everyone and useful for exactly this: seeing it work without
setting anything up. Two things follow from that.

**Everything you publish is public**, and so is everything anyone else does. Change `prefix` to
something of your own or you will be reading strangers' data and they will be reading yours.

**It is not for real use.** For anything you care about, run your own: Mosquitto on a Raspberry
Pi, or in a container, is about ten minutes of work, stays on your network, and does not go down
when a public service is busy.

## Things that catch people out

**Topics and payloads are bytes**, never strings, all the way through MQTT. `b"pulsar/readings"`
and `b"21.5"`, or `.encode()` on the way in and `.decode()` on the way out. A string where bytes
are expected fails immediately, which is at least honest.

**The client id must be unique on the broker.** Two boards using the same one kick each other
off, endlessly, and the symptom looks exactly like an unreliable network. On a public broker,
pick something nobody else would.

**`keepalive` is a promise.** You are telling the broker you will say something at least that
often; go quiet for longer and it drops you, silently from your side. This example publishes
every five seconds against a sixty second keepalive, which is a comfortable margin. If your
readings are minutes apart, call `client.ping()` in between.

**`check_msg()` looks, `wait_msg()` waits.** A loop doing anything else wants `check_msg()`,
which returns straight away. `wait_msg()` blocks until something arrives, which is fine for a
board that only reacts to commands.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| `ImportError: no module named 'umqtt'` | The driver is not installed. It is frozen into ESP32 firmware but not the Pico W's |
| It connects, then drops every minute or so | Two boards sharing a client id, or nothing published inside `keepalive` |
| `OSError: -1` or `104` on connect | The broker refused or the name did not resolve. Try the [DNS example](../wifi-dns) first |
| Published but nothing sees it | Different topics. They are compared exactly, and are case sensitive |
| Works on an ESP32, not on a Pico W | Install the umqtt driver, and try `power_save=False` on the wifi connect |

## Try changing

- **Publish a real reading.** Any of the [Sensors](../i2c-bmp280) examples drops straight in:
  read the value and publish it instead of the counter.
- **Act on the command.** Turn an LED on when the message is `on`, which is the whole of home
  automation in three lines.
- **Use a retained message** — `client.publish(topic, payload, retain=True)` — so a subscriber
  that connects later immediately gets the last value instead of waiting for the next one.
- **Give it a last will**: `client.set_last_will(topic, b"offline")` before connecting, and the
  broker announces the board's death if it disappears without saying goodbye.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
