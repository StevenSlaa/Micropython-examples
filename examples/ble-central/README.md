---
example: ble-central
author: Steven Slaa
---

# 3. A BLE Central

Finds the device from the [peripheral example](../ble-peripheral), connects to it, reads its
temperature, and then subscribes so new readings arrive without asking.

This is what the phone app was doing. Here a second board does it instead.

**You need two boards for this**, both with Bluetooth: ESP32, ESP32-S3 or Pico **W**. One runs
[2. A BLE Peripheral](../ble-peripheral); this one runs here.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

## Run it

Start the peripheral first, then this:

```
Looking for pulsar-sensor
Found at Device(ADDR_RANDOM, 28:cd:c1:0f:4a:19)
Read: 22.41 C
Subscribed; waiting for updates
Notified: 23.08 C
Notified: 21.77 C
```

The first value came from asking. Everything after it arrived on its own.

## Read, or subscribe?

```python
await characteristic.read()             # ask once, get the current value
await characteristic.subscribe(notify=True)
await characteristic.notified()         # wait for the peripheral to send the next one
```

**Read** is a question and an answer. Fine for something you want occasionally, and wasteful in
a loop: most of the answers will be a value you already had.

**Subscribe** tells the peripheral to push each new value as it happens. Nothing is spent asking,
and the radio stays quiet in between — which on a coin cell is the difference between weeks and
days.

## Matching on the name, not the address

```python
if result.name() == target_name and SERVICE_UUID in result.services():
```

BLE addresses change on purpose. Phones, watches and plenty of boards rotate theirs every few
minutes so they cannot be followed around a building. Remembering an address and reconnecting to
it later therefore often fails for no visible reason.

Matching the name and the service it offers is more robust. For something that must be *this*
device and no other, the answer is pairing, which stores a key that survives the address change.

## If it cannot find or connect

| What you see | What it usually means |
| --- | --- |
| `Not found; is the peripheral running?` | Start the peripheral first. Check it prints `Advertising` |
| Found, then `It stopped answering` | It was already connected to something else, often a phone still holding the connection from the previous example |
| Connects, then fails on `service()` | The UUIDs do not match the peripheral's |
| It works once, then not again | The peripheral is not advertising again after the disconnect |
| `ImportError: no module named 'aioble'` | Install the driver; a Pico W has it, an ESP32 does not |

## Try changing

- Stop the peripheral while this is connected, and watch what happens: `notified()` raises when
  the connection drops, and the outer loop starts looking again.
- Add a second characteristic to the peripheral — humidity is `0x2a6f` — and read both.
- Make the peripheral's characteristic writable and send a command the other way, which turns
  this into a remote control rather than a sensor.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
