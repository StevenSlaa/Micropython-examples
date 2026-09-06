---
example: ble-scan
author: Steven Slaa
---

# 1. Scanning for BLE Devices

Lists the Bluetooth Low Energy devices around you: phones, watches, headphones, thermometers,
and quite a lot of things you did not know were there.

Nothing is connected to and nothing is paired. Devices that want to be found simply advertise —
they shout a short packet every so often — and anything listening hears it. That is why this
finds a fitness band you have never met.

**Needs a board with Bluetooth**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

A Pico W has aioble in its firmware already and will run this without installing anything. An
ESP32 will not: it has Bluetooth, but not this library.

## Run it

```
Scanning for 5000 ms...
Found: 7 devices
Someone's Watch      Signal:  -52 dBm  very close Connectable: True  Services: none advertised
(no name)            Signal:  -61 dBm  nearby     Connectable: False Services: none advertised
Thermometer          Signal:  -78 dBm  in range   Connectable: True  Services: UUID(0x181a)
```

## Reading the output

**No name** is normal, and not a fault. A name does not fit in the first advertising packet, so
a device only gives one if asked — that is what `active=True` does, at the cost of an extra
exchange per device. Plenty still refuse.

**Connectable: False** means the device is announcing something and does not want to talk. A
beacon in a shop, or a phone broadcasting for tracking, looks like this.

**Services** are what the device says it offers before you connect. `0x181a` is environmental
sensing, `0x180f` battery, `0x180d` heart rate — short numbers are registered standard meanings
that any app understands. Most devices advertise none and keep their services for after you
connect.

**Signal** is dBm, always negative, closer to zero is closer to you. Roughly: above −60 is in
the same room, below −90 is not worth trying to connect to.

## Why the same devices keep changing address

Phones and watches deliberately change their Bluetooth address every few minutes so they cannot
be followed around a building. If a device appears to come and go between scans, that is usually
this rather than a range problem — which is also why the scan matches on the *name* in the
[central example](../ble-central) rather than the address.

## Try changing

- `active=False`, and count how many devices lose their names.
- `window_us=15000` with `interval_us=30000`: the radio now listens half the time, finds fewer
  devices, and uses less power. That trade is most of what tuning a scan is.
- Print `result.device.addr_hex()` and watch which addresses stay put between scans and which do
  not.

## Next

[2. A BLE Peripheral](../ble-peripheral) makes the board into one of the devices in this list.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
