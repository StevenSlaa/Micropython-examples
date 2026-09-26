---
example: ble-uart
author: Steven Slaa
---

# 5. Bluetooth UART

A serial port over Bluetooth. Type `on` in a phone app and the board's LED turns on and the
board answers `led is on`. It is the quickest way to control a project from a phone
without writing an app.

It uses the **Nordic UART Service**. It is not an official Bluetooth standard, but so many
devices copied it that every BLE terminal app speaks it.

**Needs a board with Bluetooth**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

## Run it, then talk to it

Install a BLE terminal app on the phone:

- **Android**: *Serial Bluetooth Terminal* (Kai Morich). In the menu choose *Devices →
  Bluetooth LE*, scan, and tap `pulsar-uart`.
- **iPhone or Android**: *nRF Connect*. Connect to `pulsar-uart`, open the UART tab or
  the service starting `6E400001`, and write to the RX characteristic.

On a Pico W, change the led to `Pin("LED", Pin.OUT)` first.

```
Advertising as pulsar-uart
Connected to Device(ADDR_RANDOM, 6b:02:9e:14:c0:5d)
> on
< led is on
> status
< led is on
```

Anything you send appears on the board's console with `>`, and the reply with `<`. The phone
shows the replies.

## How it works

```python
rx = aioble.Characteristic(service, RX_UUID, write=True, write_no_response=True, capture=True)
tx = aioble.Characteristic(service, TX_UUID, notify=True)
```

Two characteristics, one per direction. The phone **writes** to RX, and the board sends back
with a **notification** on TX. The names are from the board's side, so the phone app may
label them the other way round. That is the most common mix-up with this service.

`capture=True` keeps every write in a queue. Without it, aioble only keeps the latest one, so
two commands sent quickly would lose the first.

```python
for i in range(0, len(data), 20):
    tx.notify(connection, data[i:i + 20])
```

A notification holds 20 bytes unless the phone negotiates more, so longer replies go out in
pieces. Terminal apps put them back together.

## Adding commands

Everything happens in `handle()`: it gets the command as lowercase text and returns the reply.

```python
if command == "temp":
    return "%.1f C" % sensor.temperature()
```

Any sensor example drops into this. For a command with a value, such as `servo 90`, split it:
`word, value = command.split()`.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Not in the app's device list | *Serial Bluetooth Terminal* lists classic Bluetooth by default; switch to *Bluetooth LE* |
| Connects, but nothing arrives on the phone | The app has not subscribed to TX. In nRF Connect, tap the notify arrow on TX |
| `unknown command` for something you typed right | The app sends extra characters. Commands are stripped and lowercased, so check the spelling |
| Long commands arrive in two halves | Each write is treated as one command, and a write holds 20 bytes. Keep commands short, or collect them until a newline |

## Try changing

- Send sensor readings every second without being asked, as the
  [peripheral](../ble-peripheral) example does.
- Talk to it from a second board instead of a phone, the way the [central](../ble-central)
  example does, for a wireless serial link between two boards.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
