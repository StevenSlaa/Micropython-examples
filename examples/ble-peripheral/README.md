---
example: ble-peripheral
author: Steven Slaa
---

# 2. A BLE Peripheral

The board becomes a Bluetooth device. It advertises a temperature service, and anything that
connects can read the value or subscribe to be told when it changes.

This is the shape of every BLE sensor you have ever owned.

**Needs a board with Bluetooth**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

## Run it, then look with a phone

```
Advertising as pulsar-sensor
Temperature: 22.41 C
Temperature: 23.08 C
Connected to Device(ADDR_RANDOM, 4f:2c:11:9a:33:80)
```

Install **nRF Connect** (Nordic) or **LightBlue**, both free, on a phone. Scan, find
`pulsar-sensor`, connect. You will see an Environmental Sensing service with a Temperature
characteristic, and the phone will show it as an actual temperature — because the example uses
the standard UUIDs for those things.

Press subscribe or the notify arrow, and new readings arrive on their own every two seconds
without the phone asking again.

## The pieces

```python
service = aioble.Service(SERVICE_UUID)
characteristic = aioble.Characteristic(service, TEMPERATURE_UUID, read=True, notify=True)
aioble.register_services(service)
```

- A **service** is a group. A **characteristic** is one value inside it.
- **read** lets a central ask for the value. **notify** lets the board push it without being
  asked, to anything that subscribed. Most sensors offer both.
- Registering happens once, before advertising.

```python
connection = await aioble.advertise(250_000, name=name, services=[SERVICE_UUID])
await connection.disconnected()
```

`advertise()` waits until something connects and hands back the connection. When it ends, the
loop advertises again — a peripheral that does not do this can be connected to exactly once,
which is a common and confusing bug.

## Why the UUIDs matter

```python
SERVICE_UUID = bluetooth.UUID(0x181A)      # environmental sensing
TEMPERATURE_UUID = bluetooth.UUID(0x2A6E)  # temperature
```

Short UUIDs are registered standard meanings. Every BLE app in the world already knows that
`0x2a6e` is a temperature in hundredths of a degree, which is why a phone shows *22.4 °C*
rather than four unexplained bytes.

That also fixes the format for you:

```python
struct.pack("<h", int(celsius * 100))     # signed 16 bit, hundredths
```

Send something else and apps will still show a number, just a wrong one — a temperature of 8000
degrees usually means the units were skipped.

For a value with no standard meaning, invent a long UUID of your own. Only your code will know
what it means, which is fine when your code is both ends.

## Two things at once

```python
await asyncio.gather(sensor_task(), advertise_task())
```

Publishing and advertising run together. That is what aioble buys over the raw `bluetooth`
module, where both would be callbacks and sharing state between them would be your problem.

Note that the sensor task keeps running whether anything is connected or not. Writing to a
characteristic with nothing subscribed is harmless: it just updates the value that a future
reader will get.

## If a phone cannot find it

| What you see | What it usually means |
| --- | --- |
| `ImportError: no module named 'aioble'` | The driver is not installed. A Pico W has it; an ESP32 does not |
| Nothing in the scan | Some phones cache old results; pull to refresh, or restart Bluetooth |
| It appears with no name | Advertising was restarted while the phone was still showing an old entry |
| It connects once and never again | In your own code, not this one: advertising has to be started again after a disconnect |
| Connects then drops immediately | Usually another central already connected. One at a time |

## Next

[3. A BLE Central](../ble-central) connects to this from a second board, instead of a phone.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
