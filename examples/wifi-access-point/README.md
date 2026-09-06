---
example: wifi-access-point
author: Steven Slaa
---

# 3. Running an Access Point

The board stops looking for networks and becomes one. Join it with a phone, open a page, and the
board answers.

This is how a device with no screen and no keyboard gets configured: it puts up its own network,
you join it, and it shows you a form. A smart plug being set up for the first time is doing
exactly this.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Wifi and access points](../../drivers/wifi) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Run it

```
Network: pulsar-setup
Join it, then open http://192.168.4.1
Visitor 1 from 192.168.4.2
Visitor 2 from 192.168.4.2
```

Take a phone, join **pulsar-setup** with the password in the script, and open that address. The
phone will very likely complain that the network has no internet, and offer to switch back to
mobile data — say no, or nothing will reach the board.

## Why the setup order is odd

The driver configures the interface, switches it on, and then configures it again. That looks
redundant and is not:

- The **ESP32** documentation activates the interface first and configures it after.
- The **Pico W** documentation configures it first and activates it after.

Each order gives an unnamed or unprotected network on the other board. Doing both works on
either, which is the sort of thing that makes a driver worth having.

The same applies to the password: an ESP32 has to be told to use WPA2 explicitly, while a Pico W
chooses it and rejects being told. The driver asks, and carries on if refused.

## An access point is not the internet

Devices that join get an address from the board — usually 192.168.4.x, with the board itself at
192.168.4.1 — and can reach the board and each other. They cannot reach anything else, because
there is nothing behind the board to reach.

That is why phones warn about it. It is not a fault; it is what an access point without an
uplink is.

## The web page

There is no web framework here, and none is needed. A browser asking for a page sends a few
lines of text over a socket and reads a few lines back:

```
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!doctype html>...
```

The blank line between the headers and the page is required — leave it out and the browser will
sit there waiting. Reading the request before replying is also required in practice, even though
this page ignores what it says: some browsers will not render a reply to a request that was
never read.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| The network does not appear | Give it a few seconds; check the board really has wifi |
| The password is refused | It must be at least 8 characters. The driver checks, since the firmware error is obscure |
| The network appears but joining fails | On an ESP32 without the WPA2 setting the network can end up open-but-expecting-a-password. Reinstalling the driver fixes this |
| Joined, but the page will not load | The phone has switched back to mobile data. Turn it off and retry |
| It works once and then does not | A browser holding the connection open; this example serves one visitor at a time |

## Try changing

- Serve a form, read the request properly, and use it to store a network name and password in
  [EEPROM](../i2c-eeprom) — that is a real setup flow.
- Leave `password` as `None` for an open network, and see how much faster a phone joins it.
- Run this and [joining a network](../wifi-connect) at once, on both interfaces. It works, on
  one radio, and a Pico W in particular slows down noticeably.

## Next

[4. DNS and Fetching a Page](../wifi-dns) goes the other way: joining a real network and asking
it for something.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
