# Wifi and access points

Joining a wifi network, or running one, with the same code on an ESP32, an ESP32-S3 and a
Raspberry Pi Pico W.

The `network` module looks identical on all of them and is not quite. This driver is the
difference, and it is worth knowing what it papers over, because both of these produce programs
that work on the board they were written on and misbehave quietly on another.

**Status codes are numbered differently on every port**, and the ports do not even define the
same set:

| | ESP32 | Pico W |
| --- | --- | --- |
| `STAT_GOT_IP` | 1010 | 3 |
| `STAT_WRONG_PASSWORD` | 202 | −3 |
| `STAT_NO_AP_FOUND` | 201 | −2 |
| `STAT_CONNECT_FAIL` | — | −1 |
| `STAT_ASSOC_FAIL` | 203 | — |

Not one value is shared. Comparing `wlan.status()` against a number copied from a tutorial is
therefore a bug waiting for a different board. This driver reads the names out of the firmware
it is running on, so `describe()` says "wrong password" on both.

**Access points are set up in opposite orders.** The ESP32 documentation activates the
interface and then configures it; the Pico W documentation configures it and then activates.
Each order fails, or silently gives an unnamed network, on the other board. This driver does
both, which satisfies either.

## Install

Install it from the Pulsar IoT library panel, or copy `wifi.py` to `/lib` on the board.

## Joining a network

```python
import wifi

station = wifi.connect("my-network", "my-password")
print(wifi.address(station))
```

`connect()` blocks until there is an address, and raises `OSError` with a readable reason if
not: *Could not join my-network: wrong password*. A wrong password comes back straight away
rather than after the timeout, because the firmware knows immediately.

```python
try:
    station = wifi.connect(SSID, PASSWORD, timeout=20)
except OSError as error:
    print(error)     # "no ap found", "wrong password", "Timed out ... (connecting)"
```

Useful arguments:

- **`hostname="pulsar"`** — the name the board appears under on the network. Two spellings of
  this exist depending on port and version, and both are tried.
- **`power_save=False`** — worth setting on a Pico W that answers requests. Its radio sleeps
  between beacons otherwise, which shows up as replies that take hundreds of milliseconds for
  no visible reason. Costs a little current.

## Running an access point

```python
ap = wifi.access_point("pulsar-setup", "hunter2hunter")
print(wifi.address(ap))     # usually 192.168.4.1
```

Leave the password out for an open network. A password shorter than eight characters is refused
here rather than by the firmware, whose error for it is obscure.

Devices that join see the board at the address above, which is where a configuration page would
be served. An access point does not give them the internet: it is a network of its own.

## Looking at the connection

```python
wifi.address(station)     # '192.168.1.50'
wifi.details(station)     # {'ip': ..., 'netmask': ..., 'gateway': ..., 'dns': ...}
wifi.disconnect()         # leave, and switch the radio off
```

`details()` is `ifconfig()` with names on it, so the DNS server the router handed out is
readable rather than being the fourth item of a tuple.

## Notes

- The radio is on until you turn it off, and it is the largest thing a battery-powered board
  spends its current on. `wifi.disconnect()` before deep sleep.
- Both interfaces can run at once — joining a network while being an access point — but on one
  radio, and the Pico W in particular gets slow doing it.
- `connect()` returns immediately if the board is already connected, so calling it at the top of
  every program is cheap.
- Nothing here does TLS, certificates or captive portals. `requests` is in the firmware on both
  boards for HTTPS.

## Tests

`python3 -B drivers/wifi/test_wifi.py` runs the driver against two fake `network` modules
numbered exactly as the ESP32 and the Pico W really number their status codes, and checks that
both report the same words, that a wrong password is raised at once, that a timeout gives up
when it said it would, and that an access point is configured on both sides of being switched
on.

Used by: [wifi-scan](../../examples/wifi-scan), [wifi-access-point](../../examples/wifi-access-point),
[wifi-dns](../../examples/wifi-dns) and [mqtt](../../examples/mqtt)
