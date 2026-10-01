---
example: lorawan-ttn
author: Steven Slaa
---

# LoRaWAN: The Things Network

In this example the microcontroller joins [The Things Network](https://www.thethingsnetwork.org)
(TTN) over LoRaWAN and sends a counter every ten minutes. Each one appears in the TTN console, on
the internet, having gone through whichever gateway heard it. No wifi needed on the board.

**You need a TTN gateway in range.** Check the map at [ttnmapper.org](https://ttnmapper.org), or
run a gateway of your own. Without one, the join never gets an answer.

## Requires
This example needs the [SX1276/SX1278 LoRa radio](../../drivers/sx127x) and
[LoRaWAN](../../drivers/lorawan) drivers installed on the board.
> Install them from the library panel in the Pulsar IoT IDE, or copy the drivers' `.py`
> files into `/lib` on the microcontroller yourself.

An ESP32 board, or a Pico W: the firmware needs `cryptolib` for the encryption.

## Register the device

1. Sign in to the [TTN console](https://console.cloud.thethings.network) and pick the cluster
   nearest to you.
2. **Create an application**. Any ID will do.
3. **Register end device**, then **Enter end device specifics manually**:
   - **Frequency plan**: see the table below, and set `region` in the script to match.
   - **LoRaWAN version**: LoRaWAN Specification 1.0.2, regional parameters RP001 1.0.2 revision B.
   - **JoinEUI**: all zeros is fine.
   - **DevEUI** and **AppKey**: press Generate.
4. Copy **DevEUI**, **JoinEUI** and **AppKey** into the top of the script, exactly as the console
   shows them.

| `region` | Frequency plan in the console |
| --- | --- |
| `EU868` | Europe 863-870 MHz (SF9 for RX2 - recommended) |
| `US915` | United States 902-928 MHz, FSB 2 (used by TTN) |
| `AU915` | Australia 915-928 MHz, FSB 2 (used by TTN) |

## Connections

Set the pins at the top of the script to match your board. Boards with the radio built in are
already wired; for a separate RFM95 module, wire it as in the last two columns.

| Script setting | LilyGO T3 LoRa32 V1.6.1 | Heltec WiFi LoRa 32 V2 | ESP32 + RFM95 module | Pico W + RFM95 module |
| --- | --- | --- | --- | --- |
| `spi_id` | 1 | 1 | 1 | 0 |
| `sck_pin` | 5 | 5 | 18 | 2 |
| `mosi_pin` | 27 | 27 | 23 | 3 |
| `miso_pin` | 19 | 19 | 19 | 4 |
| `cs_pin` | 18 | 18 | 5 | 5 |
| `reset_pin` | 23 | 14 | 4 | 6 |

A separate module runs on **3.3V only**. The radio must be the 868/915MHz version (SX1276,
RFM95); the 433MHz SX1278 cannot reach TTN.

**Never transmit without an antenna**, it can damage the radio.

## Output
```
Joining, attempt 1
Joined, device address 260B1234
Sent: 1  Frame: 0
Sent: 2  Frame: 1
Downlink: b'\x01'
```

Joining takes about six seconds when a gateway hears it. In the console, open the device's
**Live data** tab to watch the join and each uplink arrive, with the gateways that heard it and
their signal strength.

## Seeing a number instead of hex

The console shows the payload as bytes, `00 01`. Under the application's **Payload formatters**,
**Uplink**, choose **Custom Javascript formatter** and paste:

```javascript
function decodeUplink(input) {
  return { data: { counter: (input.bytes[0] << 8) | input.bytes[1] } };
}
```

## Sending something back

On the device's **Messaging** tab, **Schedule downlink**, enter a port of 1 and a payload such as
`01`. It waits at the network until the board's next uplink, and is printed a few seconds after
it. The board can only listen straight after sending, which is what keeps LoRaWAN devices
running for years on a battery.

## Nothing arrives

- Attempts that never succeed: no gateway in range, the wrong `region`, or a key copied
  wrongly. The console's **Live data** shows a join request that reached the network even when
  it was rejected.
- Joined, but uplinks stopped: the device was deleted and registered again in the console. Delete
  `lorawan.json` from the board so it joins afresh.

## Keep it fair

TTN gives each device 30 seconds of airtime a day. That is why `interval` is ten minutes; lower
`spreading_factor` to 7 if a gateway is close, and it can send about four times as often.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
