---
example: wifi-connect
author: Steven Slaa
---

# 1. Joining a Wifi Network

Connects to a wifi network and prints what the router gave you: an address, a gateway and a DNS
server. Everything else on a network starts here.

This example uses the `network` module directly, so you can see what it does. The other
networking examples use the [wifi driver](../../drivers/wifi), which is this with the awkward
parts handled.

**Needs a board with wifi**: an ESP32, an ESP32-S3, or a Pico **W**. A plain Pico has no radio,
and `import network` fails on it — that is not a fault in the code.

## What you will learn

- The difference between joining a network and being one
- Why you should never compare `wlan.status()` against a number from a tutorial
- What the four values from `ifconfig()` are

## Set it up

Put your network's name and password at the top of the script. That is all the wiring there is.

## Run it

```
Joining your-network
Status: connecting
Status: connecting
Connected
IP address: 192.168.1.50
Netmask: 255.255.255.0
Gateway: 192.168.1.1
DNS server: 192.168.1.1
```

## How it works

```python
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
```

`STA_IF` is the *station* interface: the one that joins somebody else's network, which is what
a phone or a laptop does. The other, `AP_IF`, is for being a network yourself — that is the
[access point example](../wifi-access-point). The radio is off until `active(True)`, and
nothing works before it.

```python
wlan.connect(SSID, PASSWORD)
```

This returns straight away. Joining takes seconds, so the loop that follows is not optional.

### The status codes are the trap

```python
STATUS_NAMES = {
    getattr(network, name): name[5:].lower().replace("_", " ")
    for name in dir(network)
    if name.startswith("STAT_")
}
```

Every port numbers these differently, and they do not even define the same ones:

| | ESP32 | Pico W |
| --- | --- | --- |
| `STAT_GOT_IP` | 1010 | 3 |
| `STAT_WRONG_PASSWORD` | 202 | −3 |
| `STAT_NO_AP_FOUND` | 201 | −2 |

Not one value is shared. `if wlan.status() == 202` is therefore a bug that only shows up on
somebody else's board, and it will look like a network problem rather than a code one. Reading
the names out of the firmware, as above, is right everywhere.

### What ifconfig gives you

```python
ip, netmask, gateway, dns = wlan.ifconfig()
```

Four values in a fixed order, and easy to mix up:

- **IP address** — this board, on this network. Usually handed out by the router and not
  guaranteed to be the same next time.
- **Netmask** — which addresses count as "nearby" and can be reached directly.
- **Gateway** — where everything else is sent, which is your router.
- **DNS server** — who to ask for the address behind a name. The
  [DNS example](../wifi-dns) does exactly that.

## If it does not connect

| What you see | What it usually means |
| --- | --- |
| `wrong password` | The password. Note that it is case sensitive |
| `no ap found` | Wrong name, out of range, or a 5GHz-only network: these boards are 2.4GHz only |
| `beacon timeout`, `assoc fail` | In range but the connection is failing; often a crowded channel |
| Never leaves `connecting` | Frequently the same as `no ap found` on a board that gives up more slowly |
| `ImportError: no module named 'network'` | A board with no wifi. A plain Pico is not a Pico W |
| It connects but nothing else works | Look at the gateway and DNS above; both being blank means a network that gave out no address |

**These boards are 2.4GHz only.** A router advertising one name for both bands usually just
works; one with a separate 5GHz name will never be found.

## Try changing

- Use the wrong password on purpose, and watch how quickly the failure comes back compared with
  a network name that does not exist.
- Print `wlan.status()` alongside the name and compare the numbers with the table above.
- Add `wlan.config(hostname="pulsar")` before connecting, and look for that name in your
  router's list of devices.

## Next

[2. Scanning for Networks](../wifi-scan) shows what is around you, and is the quickest way to
find out whether the network you are trying to join is visible at all.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
