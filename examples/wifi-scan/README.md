---
example: wifi-scan
author: Steven Slaa
---

# 2. Scanning for Networks

Lists the wifi networks around you, strongest first, with the channel each is on and whether it
needs a password.

This is the first thing to run when a connection is not working: if the network you are trying
to join is not in this list, no amount of checking the password will help.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**.

## Run it

```
Scanning...
Found: 6 networks
home-network             Channel:  6  Signal:  -48 dBm  excellent, password
BTHub-4821               Channel: 11  Signal:  -67 dBm  good, password
guest                    Channel:  6  Signal:  -71 dBm  weak, open
(hidden)                 Channel:  1  Signal:  -82 dBm  barely there, password
```

Nothing has to be connected for this. The radio only has to be switched on.

## Reading the output

**Signal** is in dBm and always negative — it is a measure of how much weaker the signal is than
a reference, so closer to zero is stronger. As a rule of thumb:

| dBm | What to expect |
| --- | --- |
| −30 to −60 | Excellent. Same room |
| −60 to −70 | Good. Reliable |
| −70 to −80 | Weak. Works, drops occasionally |
| below −80 | Barely there. Expect trouble |

**Channel** matters more than people expect. 2.4GHz has three channels that do not overlap — 1,
6 and 11 — and everything else sits on top of its neighbours. If your network and three others
are all on channel 6, that is worth knowing, and it is the same crowding that affects
[nRF24 radio links](../nrf24-send), which share the band.

**Hidden** networks broadcast no name, so they appear with an empty one. They can still be
joined by typing the name exactly; hiding it is not a security measure.

## Why your network might not appear

- **It is 5GHz.** These boards are 2.4GHz only. A router with one name for both bands is fine;
  one with a separate 5GHz name will never show up here.
- **It is too far.** Anything below about −85 dBm will not be listed reliably.
- **It is hidden**, in which case look for an entry with no name on the right channel.

## A note on the security column

The last field of each entry is a number describing the authentication in use, and the ports
disagree about what those numbers mean. Only `0`, meaning open, is the same everywhere — which
is why this example only distinguishes open from not, rather than claiming to know WPA2 from
WPA3.

## Try changing

- Sort by channel instead of signal, and see how crowded each one is.
- Print `bssid` as hex: it is the access point's hardware address, and a network with several
  access points shows up as several entries with the same name.
- Walk around with the board on a battery and watch the numbers move. It is a decent way to find
  a dead spot before mounting something in one.

## Next

[3. Running an Access Point](../wifi-access-point) turns the board into one of the networks in
this list.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
