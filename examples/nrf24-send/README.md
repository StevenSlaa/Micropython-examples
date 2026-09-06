# nRF24 Radio: Sending

In this example the microcontroller sends a counter over a 2.4GHz radio link once a second, and
prints whether each packet was acknowledged by the board at the other end.

**You need two boards for this**, each with an nRF24L01+ module. This one sends; the other runs
[nRF24 Radio: Receiving](../nrf24-receive).

## Requires
This example needs the [nRF24L01+ radio](../../drivers/nrf24l01) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| Module | ESP32 | Pico |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| CE | 4 | 6 |
| CSN | 5 | 5 |
| SCK | 18 | 2 |
| MOSI | 23 | 3 |
| MISO | 19 | 4 |
| IRQ | not connected | not connected |

On a Pico, also set `spi_id = 0` at the top of the script.

## Solder a capacitor to the module

Before anything else. A 10µF capacitor across the module's VCC and GND pins, with a 100nF beside
it if you have one.

Transmitting draws a sudden burst of current, and on a breadboard the supply dips, the module
browns out, and you get symptoms that look like anything but a power problem: it works next to
the receiver but not across the room, it sends for a minute and stops, or the board resets every
time it transmits. This is the single most common reason these modules disappoint.

**Never put 5V on VCC** — it is a 3.3V part. The data pins are 5V tolerant, so a 5V board can
still talk to it.

## Output
```
Sending on channel 76
Sent: 1  Delivered: 1  Lost: 0
Sent: 2  Delivered: 2  Lost: 0
Sent: 3  Delivered: 2  Lost: 1  (no answer)
Sent: 4  Delivered: 3  Lost: 1
```

`send()` raises when nothing acknowledged, and that is the useful part: the receiving module
acknowledges in hardware, so a delivered count means the packets genuinely arrived. The chip has
already retried eight times before reporting failure.

Carry the sending board away from the receiver and watch the lost count start climbing — it is a
good way to find the real range of your setup rather than the one on the packaging.

## Nothing is delivered at all

Every one of these must match on both boards, and a mismatch usually gives silence rather than
an error:

| Setting | Symptom if it differs |
| --- | --- |
| `channel` | Nothing at all |
| `payload_size` | Nothing, or rubbish at the other end |
| Addresses | Nothing — the sender's `send_to` must be the receiver's `listen_on` |

Beyond that: is the other board actually running the receiving example? Is the capacitor
fitted? And try another channel — WiFi crowds the bottom of the band, so anything above 76 is
usually quieter.

## Plotter

Open the **Plotter** tab beside the REPL to graph delivered against lost. Walking away from the
receiver draws the moment the link starts to fail far more clearly than the numbers do.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
