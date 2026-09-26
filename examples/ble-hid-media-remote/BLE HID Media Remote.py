# A Bluetooth media remote: buttons on the board control music and volume on a phone or PC.
#
# The board pretends to be a keyboard with only media keys, using HID over GATT: the same
# standard every Bluetooth keyboard and mouse uses. That is why no app is needed. Android,
# iOS, Windows, macOS and Linux all already know what to do with it.

import asyncio
import struct
from machine import Pin
import aioble
import aioble.security
import bluetooth

# --- Configuration ---------------------------------------------------------------------------
# the name that appears in the phone's Bluetooth settings
name = "pulsar-remote"

# The keys this remote can send, one bit each, in the same order as the report map below.
VOLUME_UP = 0x01     # on an iPhone, this also takes a photo in the camera app
VOLUME_DOWN = 0x02
MUTE = 0x04
PLAY_PAUSE = 0x08
NEXT = 0x10
PREVIOUS = 0x20

# which button sends which key. GPIO 0 is the BOOT button on most ESP32 boards. Buttons
# connect the pin to GND; the internal pull-up does the rest.
buttons = {
    0: PLAY_PAUSE,
    # 12: VOLUME_UP,
    # 13: VOLUME_DOWN,
    # 14: NEXT,
}
# ----------------------------------------------------------------------------------------------

# The report map is how an HID device describes itself: "I send one byte, and each bit is one
# of these keys". The host reads it once and then understands every report that follows.
REPORT_MAP = bytes((
    0x05, 0x0C,        # Usage Page (Consumer): media keys, not letters
    0x09, 0x01,        # Usage (Consumer Control)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x01,        #   Report ID (1)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1): each key is up or down
    0x75, 0x01,        #   Report Size (1 bit)
    0x95, 0x06,        #   Report Count (6 keys)
    0x09, 0xE9,        #   Usage (Volume Up)        bit 0
    0x09, 0xEA,        #   Usage (Volume Down)      bit 1
    0x09, 0xE2,        #   Usage (Mute)             bit 2
    0x09, 0xCD,        #   Usage (Play/Pause)       bit 3
    0x09, 0xB5,        #   Usage (Next Track)       bit 4
    0x09, 0xB6,        #   Usage (Previous Track)   bit 5
    0x81, 0x02,        #   Input (Data, Variable, Absolute)
    0x95, 0x02,        #   Report Count (2)
    0x81, 0x01,        #   Input (Constant): two unused bits, to fill the byte
    0xC0,              # End Collection
))

# HID over GATT asks for three services: HID itself, device information, and battery.
hid = aioble.Service(bluetooth.UUID(0x1812))
aioble.Characteristic(hid, bluetooth.UUID(0x2A4A), read=True,   # HID information:
                      initial=struct.pack("<HBB", 0x0111, 0, 0x02))   # HID 1.11, can wake
# the default buffer is 20 bytes and the report map is longer
report_map = aioble.BufferedCharacteristic(hid, bluetooth.UUID(0x2A4B), read=True,
                                           max_len=len(REPORT_MAP))
aioble.Characteristic(hid, bluetooth.UUID(0x2A4C), write_no_response=True)   # control point
report = aioble.Characteristic(hid, bluetooth.UUID(0x2A4D), read=True, notify=True,
                               initial=b"\x00")
# which report this is: id 1, as in the report map, and 1 for input (board to host)
aioble.Descriptor(report, bluetooth.UUID(0x2908), read=True, initial=b"\x01\x01")

device_info = aioble.Service(bluetooth.UUID(0x180A))
# PnP ID: who made it. Zeros is "nobody in particular", which hosts accept.
aioble.Characteristic(device_info, bluetooth.UUID(0x2A50), read=True,
                      initial=struct.pack("<BHHH", 0x02, 0, 0, 1))

battery = aioble.Service(bluetooth.UUID(0x180F))
aioble.Characteristic(battery, bluetooth.UUID(0x2A19), read=True, notify=True,
                      initial=b"\x64")   # 100%; hosts show this next to the device name

# The host remembers the board, so the pairing keys are kept in a file across resets.
aioble.security.load_secrets()
aioble.register_services(hid, device_info, battery)
# written after registering, when the buffer is already big enough; an initial= value would be
# written before, and cut off at 20 bytes
report_map.write(REPORT_MAP)
# Hosts insist on pairing with a keyboard. No screen and no keypad means no PIN: the phone
# just asks "Pair?".
aioble.config(bond=True, le_secure=True, io=3)   # 3: no input, no output

connected = False


async def press(key):
    """A key press is two reports: the key down, then nothing down."""
    report.write(bytes((key,)), send_update=True)
    await asyncio.sleep_ms(20)
    report.write(b"\x00", send_update=True)


async def button_task():
    """Watches every button and sends its key on each press."""
    pins = {Pin(number, Pin.IN, Pin.PULL_UP): key for number, key in buttons.items()}
    was_pressed = {pin: False for pin in pins}
    while True:
        for pin, key in pins.items():
            pressed = pin.value() == 0
            if pressed and not was_pressed[pin] and connected:
                await press(key)
                print("Sent key", hex(key))
            was_pressed[pin] = pressed
        await asyncio.sleep_ms(20)


async def advertise_task():
    global connected
    while True:
        print("Advertising as", name)
        connection = await aioble.advertise(
            100_000,
            name=name,
            services=[bluetooth.UUID(0x1812)],
            appearance=0x03C1,   # keyboard, which decides the icon the host shows
        )
        print("Connected to", connection.device)
        connected = True
        await connection.disconnected(timeout_ms=None)
        connected = False
        print("Disconnected")


async def main():
    await asyncio.gather(advertise_task(), button_task())


asyncio.run(main())
