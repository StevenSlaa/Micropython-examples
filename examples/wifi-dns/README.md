---
example: wifi-dns
author: Steven Slaa
---

# 4. DNS and Fetching a Page

Turns names into addresses, and then asks one of them for a page.

Every connection to a name does this first, and it usually happens invisibly inside whatever
library you are using. Doing it on its own is worth the five minutes, because when a board
cannot reach something, "the name could not be looked up" and "the server did not answer" are
completely different problems with completely different fixes.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Wifi and access points](../../drivers/wifi) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Run it

```
Connected as 192.168.1.50
Asking the DNS server at 192.168.1.1

example.com                93.184.215.14    Lookup: 34 ms
micropython.org            176.58.119.26    Lookup: 12 ms
raspberrypi.com            104.22.64.29     Lookup: 11 ms
not-a-real-name.invalid    could not be resolved ([Errno -202] )  Lookup: 41 ms

Fetching http://example.com/
Reply: HTTP/1.1 200 OK
Bytes: 1608
```

The first lookup is slower than the rest because the answers are cached after it — by the
router, and often by the board.

## What DNS is

Computers reach each other by address; people use names. DNS is the lookup between the two.

Your board did not choose who to ask. When it joined the network it was handed four things, and
the fourth was a DNS server — usually the router itself, which asks somebody else in turn.
That is the address printed above, and it comes from `wifi.details(station)["dns"]`.

```python
socket.getaddrinfo("example.com", 80)
```

That is the whole of it. It returns a list of ways to reach the name, because a name can have
several addresses; each entry's last item is the `(address, port)` pair you would connect to.

A name that does not exist raises `OSError` **here**, before anything is connected to. That is
the useful distinction: a failure at this line is a name or a DNS problem, and a failure at the
`connect()` below is the server or the route.

## Fetching the page

There is no library involved, and none is needed to see what a request is:

```
GET / HTTP/1.1
Host: example.com
Connection: close

```

Three lines and a blank one. The **Host** header is not optional — one address often serves
hundreds of sites, and that header is what says which of them you want. The blank line at the
end is what marks the request as finished.

For real work, `requests` is already in the firmware on both an ESP32 and a Pico W and handles
HTTPS, redirects and JSON:

```python
import requests
print(requests.get("https://micropython.org").status_code)
```

This example uses a socket because that shows what `requests` is doing for you.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Every name fails to resolve | No DNS server, or no route to it. Check the address printed at the top is not blank |
| Names resolve but the fetch times out | DNS is fine; the board cannot reach the internet. Usually the gateway or a captive portal |
| Only some names fail | Genuinely that: a name that does not exist, or a filtered one |
| `-202` or `-2` on every lookup | The board thinks it is connected but has no working route. Try rejoining |
| It works, then stops after a while on a Pico W | Power saving. Pass `power_save=False` to `wifi.connect` |

## Try changing

- Look up the same name twice and compare the times. The second is cached and much faster.
- Point at a name on your own network — your router's name, or another machine — and see the
  local address come back.
- Swap the socket for `requests.get(...)` and notice how much it was doing on your behalf.

## Next

[5. MQTT](../mqtt) uses all of this to talk to a broker, which is how most small devices
actually send their readings anywhere.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
