---
example: ttgo-lora32-meshtastic-chat
author: Steven Slaa
---

# TTGO LoRa32: Meshtastic Chat

In this example a LilyGO/TTGO T3 LoRa32 V1.6.1 opens a wifi network of its own. Join it with a
phone, open the chat page, and every message typed there goes out over LoRa, kilometres rather
than metres, with no internet or phone network anywhere in the chain.

It speaks [Meshtastic](https://meshtastic.org), so it chats with:

- **your second T3 board** running this same example, each with its own phone;
- **any Meshtastic device** in range on its default settings, and the Meshtastic app on the phone
  paired to it.

## Requires
This example needs the [SX1276/SX1278 LoRa radio](../../drivers/sx127x),
[Meshtastic](../../drivers/meshtastic), [SSD1306 OLED](../../drivers/ssd1306) and
[wifi](../../drivers/wifi) drivers installed on the board.
> Install them from the library panel in the Pulsar IoT IDE, or copy the drivers' `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

None: the radio, display and LED are wired on the board. **Screw the antenna on first**;
transmitting without one can damage the radio.

Set `region` at the top of the script to where you are: `EU_868` in Europe, `US` in the Americas,
`ANZ` in Australia and New Zealand. It has to match your board's band and the other devices.

## Chatting

1. Run the script. The OLED shows the wifi name, `Meshtastic-B7C4` or similar, and the address.
2. Join that network with a phone. It has no internet, so the phone may ask whether to stay
   connected: say yes.
3. Open **http://192.168.4.1** in the browser.
4. Put your name in the top corner if you like; it goes in front of each message, which helps
   when several phones share one board.

The page shows messages as they arrive, with the signal strength of each, and a counter while you
are near the 200-byte limit. The OLED shows the newest ones too, and the green LED blinks when a
message comes in.

Run the same script on the second board, join its wifi with another phone, and the two can talk.
Each board names its wifi after its own ID, so the two networks do not clash.

## With Meshtastic devices

A Meshtastic device on its default settings — the LongFast preset, on its primary channel — sees
messages from this board in the app's main channel chat, from a node called `T3 Chat b7c4`. Its
replies appear on the chat page. Nothing needs configuring on either side except the region.

For a private channel, see the [Meshtastic driver](../../drivers/meshtastic) README: the channel
name and key go into the `Meshtastic(...)` line.

## Output
```
Meshtastic node T3 Chat b7c4 (!a3f2b7c4) on 869.525 MHz
Join the wifi network Meshtastic-B7C4 and open http://192.168.4.1
[me] Steven: hallo mesh
[Garden node] Hoi terug!
```

## Notes

- The wifi network is open by default, so anyone nearby can join and chat. Set `password` (eight
  characters or more) to stop that.
- This board chats but does not relay other nodes' messages. Meshtastic devices around it do.
- Direct messages from the Meshtastic app do not arrive here: since Meshtastic 2.5 they use
  encryption this example does not do. Use the channel chat.
- Sending takes about half a second on air. The page says "Sending over LoRa" meanwhile.
- The OLED's font is plain ASCII, so emoji show on the phone but not on the board's screen.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
