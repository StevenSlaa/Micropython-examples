---
example: ttgo-lora32-link
author: Steven Slaa
---

# TTGO LoRa32: Radio Link

In this example two LilyGO/TTGO T3 LoRa32 V1.6.1 boards find each other over LoRa and show the
link between them live on their OLEDs. Put an SD card in either one and it logs every packet too.

**Run the same script on both boards.** There is nothing to set up per board: each one takes its
name from the ESP32's unique ID, and they find each other by themselves.

## Requires
This example needs the [SX1276/SX1278 LoRa radio](../../drivers/sx127x) and
[SSD1306 OLED](../../drivers/ssd1306) drivers installed on the board.
> Install them from the library panel in the Pulsar IoT IDE, or copy the drivers' `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

None: the radio, the display, the LED, the card slot and the battery input are all wired on the
board. **Screw the antennas on first**; transmitting without one can damage the radio.

Check `frequency` at the top of the script against the band your board was sold for: 868MHz in
Europe, 915MHz in the Americas and Australia, 433MHz for the SX1278 version.

## What you see

It opens with radio waves rising from an antenna, then:

**Searching.** A radar sweeps while the board sends a beacon every five seconds and listens for
the other one. The left shows how many beacons have gone out; the right, the spreading factor and
frequency. Once a link drops, the bottom line counts how long ago the other board was last heard.

**Linked.** As soon as a beacon arrives:

- The signal strength in large figures, in dBm, with the SNR beside it.
- A graph of the last 64 beacons, so walking away draws the signal sinking.
- A bottom line that cycles through: the other board's name and counter, **how well it hears
  you**, the share of beacons lost, and the SD card's row count.

Along the top: this board's name, arrows that flash as a beacon goes out and one comes in, signal
bars, the SD card while it is logging, and the battery. The green LED blinks for each beacon heard.

Every beacon carries the signal strength its sender last heard, so each board knows both
directions of the link. They are rarely the same: one end's antenna, position or noise usually
makes one direction the weaker, and that is the one that limits the range.

## The SD card

Optional, and picked up whenever one is pushed in — checked every ten seconds. Each packet heard
adds a row to `lora_link.csv`:

```
uptime_s,peer,seq,rssi_dbm,snr_db,they_hear_dbm,missed
45,1B7C,9,-87,7.2,-80,0
50,1B7C,10,-88,6.9,-81,0
```

Open it in a spreadsheet afterwards to chart a walk. Pulling the card out is noticed on the next
write, and logging stops until one is pushed back in. The card must be FAT32.

## Output
```
LoRa link A3F2 on 868.0 MHz
RSSI: -87  SNR: 7.2  They hear: -80  Missed: 0
RSSI: -88  SNR: 6.9  They hear: -81  Missed: 0
```

## Plotter

Open the **Plotter** tab to graph both directions of the link against each other, with lost
beacons alongside. SNR is on a smaller scale, so it hugs the zero line.

## Taking it further

- **Range test.** Leave one board at a window and carry the other on its battery. The bottom line
  and graph tell you when you are near the edge: RSSI around -120, SNR well below zero, losses
  climbing.
- **More range.** Set `spreading_factor` to 10 or 12 on both boards, and raise `interval_ms` to
  match: each step doubles the airtime, and Europe allows 1% of the time on air.
- **Battery reading off?** Trim `battery_scale` against a multimeter.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
