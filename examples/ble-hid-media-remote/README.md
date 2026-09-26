---
example: ble-hid-media-remote
author: Steven Slaa
---

# 6. Bluetooth Media Remote (HID)

The board becomes a Bluetooth media remote. Press a button and the music on your phone pauses,
skips or gets louder. There is no app: the board acts as a keyboard with only media keys, and
every phone and computer already knows how to use one.

This works because it uses **HID over GATT**, the same Bluetooth standard every wireless
keyboard and mouse uses.

**Needs a board with Bluetooth**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

## Wiring

The BOOT button on an ESP32 board already works as play/pause. For more keys, wire a button
from a pin to GND for each one and add it to `buttons`:

```python
buttons = {
    0: PLAY_PAUSE,
    12: VOLUME_UP,
    13: VOLUME_DOWN,
    14: NEXT,
}
```

A Pico W has no usable button on board, so wire one and put its pin number here.

## Run it, then pair

1. Run the example. It prints `Advertising as pulsar-remote`.
2. On the phone or computer, open the **Bluetooth settings** and tap `pulsar-remote`. It
   shows up as a keyboard.
3. Accept the pairing. There is no PIN, because the board has no screen to show one.
4. Play some music and press the button.

```
Advertising as pulsar-remote
Connected to Device(ADDR_RANDOM, 71:4a:0e:bd:23:9c)
Sent key 0x8
```

The pairing is remembered in `ble_secrets.json`, so after a reset the phone reconnects by
itself.

**Party trick:** on an iPhone, and most Android phones, *volume up* takes a photo in the
camera app. That turns this into a remote shutter.

## How it works

### The report map

```python
0x05, 0x0C,        # Usage Page (Consumer): media keys, not letters
0x95, 0x06,        #   Report Count (6 keys)
0x09, 0xE9,        #   Usage (Volume Up)        bit 0
```

An HID device starts by describing itself. The **report map** says "I send one byte, and each
bit is one of these six keys". The host reads it once when it connects, and from then on knows
what every byte means. The codes come from the USB HID usage tables, the same ones a USB
keyboard uses.

### A key press

```python
report.write(bytes((key,)), send_update=True)   # key down
await asyncio.sleep_ms(20)
report.write(b"\x00", send_update=True)          # nothing down
```

A report says which keys are down *right now*. A press is two reports, one with the key and
one without. Forget the second and the host thinks the key is held: volume goes all the way
up.

### The services

HID over GATT expects three services, and some hosts refuse a device that is missing one:

| Service | What is in it |
| --- | --- |
| HID `0x1812` | The report map, the reports, and some fixed information |
| Device Information `0x180A` | Who made it (zeros here: nobody in particular) |
| Battery `0x180F` | A battery level the phone shows next to the name. Always 100% here |

### Pairing

```python
aioble.config(bond=True, le_secure=True, io=3)
```

Hosts will not use a keyboard that has not paired, since a keyboard can type your password.
`io=3` tells them the board has no screen or keypad, so there is no PIN to check: the phone
just asks *Pair?*.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Not in the Bluetooth settings | It is already paired with another device. A keyboard pairs with one host at a time |
| `Sent key` is printed, but the phone never asked to pair | The phone remembers an older version of the board. *Forget* `pulsar-remote` and connect again |
| Pairs, then nothing happens on a press | Something else is playing media, or no media app is open to receive the key |
| Worked before a reset, now does not reconnect | `ble_secrets.json` was lost. On the host, *forget* `pulsar-remote` and pair again |
| Volume keeps going up | The release report was not sent. Keep the `b"\x00"` write |
| `ValueError` or `OSError` at `config(bond=...)` | The firmware was built without pairing support. Update MicroPython |
| Changed the report map, now it misbehaves | Hosts remember the old map. Forget the device and pair again |

## Try changing

- Use a [rotary encoder](../rotary-encoder) as a volume knob: send `VOLUME_UP` or
  `VOLUME_DOWN` per step.
- Make it type text: that needs a keyboard report map (usage page `0x07`) with a modifier byte
  and key codes. The structure of this example stays the same.
- Send the real battery level by reading the battery voltage with the
  [analog read](../analog-read) example and writing it to the battery characteristic.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
