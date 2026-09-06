---
driver: aioble
author: Jim Mussared
---

# Bluetooth LE (aioble)

`aioble` is the library MicroPython recommends for Bluetooth Low Energy. It sits on top of the
built-in `bluetooth` module and replaces its interrupt callbacks with `asyncio`, which turns
code that was a state machine into code that reads top to bottom.

**A Pico W already has this**, frozen into its firmware. **An ESP32 does not** — it has the
`bluetooth` module underneath but not aioble, so the same program fails at the import.

Installing this fills that gap. On a Pico W the installed copy simply takes precedence over the
frozen one, which is harmless.

## Install

Install it from the Pulsar IoT library panel, or copy the whole `aioble/` folder to `/lib/` on
the board. It is a package: the folder matters, and `aioble/__init__.py` is what makes the
import work.

It is nine files and about 70KB, most of which is only read when you use that part of it.

## Being a device others connect to

```python
import asyncio, aioble, bluetooth

SERVICE = bluetooth.UUID(0x181A)          # environmental sensing
CHARACTERISTIC = bluetooth.UUID(0x2A6E)   # temperature

service = aioble.Service(SERVICE)
temperature = aioble.Characteristic(service, CHARACTERISTIC, read=True, notify=True)
aioble.register_services(service)

async def main():
    while True:
        async with await aioble.advertise(250_000, name="pulsar", services=[SERVICE]) as connection:
            print("Connected to", connection.device)
            await connection.disconnected()

asyncio.run(main())
```

`advertise()` waits until something connects and hands back the connection. Writing to a
characteristic with `send_update=True` pushes the new value to whatever has subscribed.

## Finding and connecting to one

```python
async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
    async for result in scanner:
        if result.name() == "pulsar":
            device = result.device
            break

connection = await device.connect()
service = await connection.service(SERVICE)
characteristic = await service.characteristic(CHARACTERISTIC)
print(await characteristic.read())
```

## What BLE actually is

Worth knowing before the examples, because the words are not obvious:

- A **peripheral** advertises and waits. A **central** scans and connects. A board can be
  either; a phone is almost always the central.
- A peripheral offers **services**, each holding **characteristics**. A characteristic is one
  value with a name, which can be read, written, or pushed to a subscriber as a **notification**.
- Names are **UUIDs**. Short ones like `0x181A` are registered standard meanings — that one is
  "environmental sensing" — and any app knows what they are. A long one you invent is for your
  own thing, and only your own code will know what it means.
- BLE is built for small values sent rarely: a temperature, a button, a battery level. It is not
  a way to move a file.

## Notes

- Everything here needs `asyncio`, which is in the firmware on both boards.
- A characteristic's value is bytes. `struct.pack` on the way in and `unpack` coming out, or
  plain text if you would rather read it in a phone app.
- Both boards do BLE only, not classic Bluetooth: no audio, no serial port profile, no pairing
  with a laptop as a keyboard.
- Scanning and advertising both use the radio, and on a Pico W so does wifi. Doing all of it at
  once works but slows everything down.
- `active=True` when scanning asks each device for its name, which costs an extra exchange per
  device. Without it, most results have no name at all.

## Credits

From [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble),
MIT, Copyright 2021 Jim Mussared, vendored unchanged.

Used by: [ble-scan](../../examples/ble-scan), [ble-peripheral](../../examples/ble-peripheral)
and [ble-central](../../examples/ble-central)
