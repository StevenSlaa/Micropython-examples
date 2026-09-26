---
example: wifi-captive-portal
author: Steven Slaa
---

# 6. Captive Portal

Join the board's network with a phone and a setup page opens by itself. Nobody has to type an
address.

This is what hotel wifi does, and what a smart plug does the first time you set it up. It is
[the access point](../wifi-access-point) again, with one extra trick: the board also answers
name lookups, and it answers every one of them with itself.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**.

## Requires
This example needs the [Wifi and access points](../../drivers/wifi) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Run it

```
Network: pulsar-setup
Join it with a phone; the setup page should open by itself
Received network 'home', password of 12 characters
```

Join **pulsar-setup**. Within a few seconds the phone shows a "Sign in to network" notice, or
opens the page straight away. Fill it in, press Save, and the board prints what it got.

## How the page opens by itself

The moment a phone joins a network, it checks whether it has internet by fetching a known page:

| Phone | Asks for |
| --- | --- |
| Android | `http://connectivitycheck.gstatic.com/generate_204` |
| iPhone, Mac | `http://captive.apple.com/hotspot-detect.html` |
| Windows | `http://www.msftconnecttest.com/connecttest.txt` |

It knows exactly what the reply should be. Anything else, and it assumes somebody is standing
between it and the internet with a page to show — and shows that page.

So the board has to do two things:

1. **Answer the lookup.** The phone first asks "where is connectivitycheck.gstatic.com?". When
   it joined, the board handed it the board itself as its DNS server, so the question comes
   here, and the answer is always *4.3.2.1*.
2. **Answer the page wrongly.** The phone then asks the board for `/generate_204`, and gets a
   redirect to `http://4.3.2.1/` instead of the empty reply it expected. That is the signal.

Every name leads to the board, and every page on every name leads to the form. There is no way
out of it, which is where "captive" comes from.

That handing out is not automatic. An ESP32 tells phones their DNS server is `0.0.0.0` unless
it is set, which is what the `ap.ifconfig(...)` line is for. Without it the phone asks nobody,
gets no answer, and quietly decides the network simply has no internet.

## Why 4.3.2.1

An access point normally sits at 192.168.4.1, and the [access point example](../wifi-access-point)
leaves it there. This one moves it, because newer Android — Samsung phones in particular — looks
at the answer to its lookup and, if it is a private address such as 192.168.x.x, never sends the
check at all. It goes straight to "Connected without internet", with no pop-up.

An address that looks public gets the check sent, and the pop-up follows. 4.3.2.1 does belong to
somebody on the real internet, but there is no internet behind the board, so nothing can clash.

## DNS in one packet

A DNS server sounds like a large thing to write. For this it is not: a query is one UDP packet,
and the answer is the same packet with a few bytes changed and an address stuck on the end.

```
query:   id | flags | 1 question | 0 answers | question
answer:  id | "response" | 1 question | 1 answer | question | "that name: 4.3.2.1"
```

The only care needed is where the question ends, since phones often add an extra record after
it that the answer must not repeat. Queries for anything other than an IPv4 address — the
`AAAA` a phone asks for at the same time, for IPv6 — get an empty answer, and the phone moves on.

## Two servers, one loop

The DNS server and the web server each wait for something to arrive, and a plain `accept()` or
`recvfrom()` would wait forever on one while the other went unanswered. `select.poll` waits on
both at once and reports which one is ready. No threads, no `asyncio`.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Nothing pops up, and the phone says "no internet" | Either the phone was not given the board as its DNS server, or `address` was set back to a private one like 192.168.4.1. Check both, then forget the network on the phone and join again |
| On a Pico W, phones cannot join once `address` is changed | Its DHCP server may keep handing out 192.168.4.x. Set `address` to `"192.168.4.1"`: the portal works, but Samsung phones will not pop up |
| Nothing pops up | Some phones take ten seconds or more. Open any `http://` address, not `https://`, and you should land on the form |
| An `https://` address shows a certificate error | Expected. The board cannot pretend to be a secure site, and should not be able to |
| The page opens, then the phone drops the network | It decided there is no internet and left. Turn off "switch to mobile data" or "auto-reconnect" for this network |
| `EADDRINUSE` when it starts | The previous run is still holding the port. Reset the board |
| The pop-up stays after saving | The phone is still getting the wrong reply to its check. Normal for this example; a real device switches the access point off once it has what it needs |

## Try changing

- Pass what the form received to `wifi.connect` and see if it works — that is the whole setup
  flow of a smart plug. Store it in [EEPROM](../i2c-eeprom) so it survives a restart.
- Add an LED or a sensor reading to the page, and it becomes a control panel with no app to
  install.
- Give the network a password, and notice the portal still opens after joining.

## Tested
- ESP32-C3 (MicroPython 1.29) with a Samsung Galaxy S25+ (Android 16): the "Sign in to network"
  notification appears on joining and opens the form. At 192.168.4.1 it did not, which is why
  the address is 4.3.2.1.
- Not yet tried on a Pico W, or with an iPhone. If you do, add it here.
