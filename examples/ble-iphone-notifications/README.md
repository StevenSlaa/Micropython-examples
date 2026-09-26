---
example: ble-iphone-notifications
author: Steven Slaa
---

# 4. iPhone Notifications

The board receives an iPhone's notifications, the way a smartwatch does: which app, the title
and the message, the moment they arrive. Press a button and the latest one is dismissed on the
phone too, or an incoming call is declined.

iOS has this built in, as the **Apple Notification Center Service (ANCS)**. There is no app to
install. Android has nothing equivalent, so this one is iPhone only.

**Needs a board with Bluetooth**: an ESP32, an ESP32-S3, or a Pico **W**. And an iPhone.

## Requires
This example needs the [Bluetooth LE (aioble)](../../drivers/aioble) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `aioble` folder
> into `/lib/` on the microcontroller yourself.

## Run it, then pair the iPhone

1. Run the example. It prints `Advertising as pulsar-notify`.
2. On the iPhone, open **Settings → Bluetooth**. `pulsar-notify` appears under *Other Devices*.
   Tap it.
3. Accept the pairing request. iOS then asks whether to **allow notifications** on the
   device. Allow it.
4. Send yourself a message.

```
Advertising as pulsar-notify
Connected to Device(ADDR_RANDOM, 5a:11:e0:3c:92:7b)
Listening for notifications

[Social] com.apple.MobileSMS
Mom
Dinner at 6?
```

The pairing is remembered in `ble_secrets.json` on the board, so after a reset the iPhone
reconnects by itself with no questions asked.

## How it works

It is the other way round from the [peripheral](../ble-peripheral) example. The board still
advertises and the phone still connects, but it is the **phone** that offers the service and
the **board** that reads from it, like the [central](../ble-central) does.

```python
solicit = bytes((17, 0x15)) + bytes(ANCS_UUID)
```

The advertisement carries a *service solicitation*: "I would like you to offer ANCS". That is
what gets the board listed in the iPhone's settings. aioble has no option for it, so the
advertisement is built by hand.

```python
await connection.pair(bond=True)
```

ANCS only shows up on an encrypted connection, so the board pairs first. `bond=True` saves the
keys, which is why it is only asked once.

ANCS then has three characteristics:

| Characteristic | Direction | What it is for |
| --- | --- | --- |
| Notification Source | phone → board | "notification 7 was added, it is Social" — 8 bytes, no text |
| Control Point | board → phone | "tell me about notification 7", or "dismiss it" |
| Data Source | phone → board | the answer: app, title, message |

So each notification is a little conversation: the phone announces it, the board asks for the
text, the phone sends it.

```python
request = struct.pack("<BIBBHBH", 0, uid, APP, TITLE, title_max, MESSAGE, message_max)
```

Command 0 asks for a notification's attributes. Title and message need a maximum length; the
app identifier does not. The answer is usually longer than one BLE packet, so it arrives in
pieces, and `parse()` returns `None` until all of it is there.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Not listed in the iPhone's Bluetooth settings | Settings only lists devices that solicit a service it offers. Leave that screen and come back |
| `ValueError` or `OSError` at `pair()` | The firmware was built without pairing support. Update MicroPython |
| `Lost the phone: TimeoutError` right after connecting | The pairing request was not accepted in time |
| `The phone offered no ANCS` | It is not an iPhone, or pairing did not encrypt the connection |
| Connects, but no notifications | Notifications were not allowed. In Settings → Bluetooth, tap ⓘ next to the board and turn on *Share System Notifications* |
| Stopped working after re-flashing | `ble_secrets.json` was lost, so the keys no longer match. On the iPhone, *Forget This Device* and pair again |

## Try changing

- `show_existing = True` shows every notification already on the phone when it connects.
- Print to a display instead: the [ST7789](../spi-st7789-display) or
  [OLED](../oled-042-esp32c3) examples show how, and the three `print` lines at the
  end of `print_notifications()` are all that change.
- Beep the [piezo](../piezo-buzzer) on an incoming call: category 1.
- Answer calls instead of declining them: the last byte of the action command is `0`.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
