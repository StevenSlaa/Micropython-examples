# nRF24 Radio: Receiving

In this example the microcontroller listens for packets on a 2.4GHz radio link, prints the
counter inside each one, and keeps a tally of any that went missing.

**You need two boards for this**, each with an nRF24L01+ module. This one listens; the other
runs [nRF24 Radio: Sending](../nrf24-send).

## Requires
This example needs the [nRF24L01+ radio](../../drivers/nrf24l01) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Identical to the sending board — see [the sending example](../nrf24-send) for the table, and for
the capacitor that these modules need across their supply.

| Module | ESP32 | Pico |
| --- | --- | --- |
| CE | 4 | 6 |
| CSN | 5 | 5 |
| SCK | 18 | 2 |
| MOSI | 23 | 3 |
| MISO | 19 | 4 |

## The configuration must match

The block at the top of both scripts has to agree: same channel, same payload size, and the
addresses swapped over. This board listens on the address the other one sends to.

Addresses are five bytes and entirely arbitrary — they are names, not routes. Change both boards
to a pair of your own and two other people's radios in the same room will not hear you.

## Output
```
Listening on channel 76
Counter: 1  Missed: 0
Counter: 2  Missed: 0
Counter: 4  Missed: 1
Counter: 5  Missed: 1
```

The counter comes from the sender and goes up by one each time, so a gap means a packet was lost
between the two boards.

Worth knowing: the sender may well believe those packets were delivered. It is told a packet
arrived when the receiving *module* acknowledges it in hardware, which happens before this
script ever sees it. A packet lost after that — because the board was busy, or the buffer was
full — is invisible from the other end. That is why this example counts them here.

## Plotter

Open the **Plotter** tab beside the REPL to watch the counter climb steadily and the missed
tally step up whenever something is lost. Walking the sending board away from this one draws the
edge of your range.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
