# Showing an iPhone's notifications on the board, the way a smartwatch does it.
#
# iOS has a built-in service for exactly this, the Apple Notification Center Service (ANCS).
# The board advertises that it wants it, the iPhone connects and pairs, and from then on every
# notification arrives here: app, title and message. A button dismisses the latest one.
#
# Android has no equivalent built in, so this is iPhone only.

import asyncio
import struct
from collections import deque
from machine import Pin
import aioble
import aioble.security
import bluetooth

# --- Configuration ---------------------------------------------------------------------------
# the name that appears in the iPhone's Bluetooth settings
name = "pulsar-notify"

# a button that dismisses the latest notification (or declines a call). GPIO 0 is the BOOT
# button on most ESP32 boards. Set it to None if you have no button.
button_pin = 0

# Notifications already on the phone are all sent again on every connection. Set this to True
# to show them too, rather than only the new ones.
show_existing = False

# the longest title and message to ask for, in bytes. iOS cuts them off with an ellipsis.
title_max = 64
message_max = 128
# ----------------------------------------------------------------------------------------------

# The three UUIDs Apple publishes for ANCS. They are long because it is Apple's own service.
ANCS_UUID = bluetooth.UUID("7905F431-B5CE-4E99-A40F-4B1E122D00D0")
NOTIFICATION_SOURCE_UUID = bluetooth.UUID("9FBF120D-6301-42D9-8C58-25E699A21DBD")
CONTROL_POINT_UUID = bluetooth.UUID("69D1D8F3-45E1-49A8-9821-9BBDFDBAD9D9")
DATA_SOURCE_UUID = bluetooth.UUID("22EAC6E9-24D6-4BB5-BE44-B36ACE7C7BFB")

# what the category number in each notification means, in Apple's order
CATEGORIES = ("Other", "Incoming call", "Missed call", "Voicemail", "Social", "Schedule",
              "Email", "News", "Health", "Finance", "Location", "Entertainment")

# the attributes asked for: which app, the title and the message
APP, TITLE, MESSAGE = 0, 1, 3

# the notification the button acts on
latest_uid = None

# The pairing keys are kept in a file, so the iPhone is remembered after a reset. This has to
# happen before Bluetooth starts.
aioble.security.load_secrets()


def advertising_data():
    """The advertisement, built by hand because aioble has no option for a solicitation.

    A solicitation says "I would like the phone to offer this service", which is what makes an
    iPhone list the board in its Bluetooth settings and offer ANCS once connected.
    """
    flags = b"\x02\x01\x06"
    solicit = bytes((17, 0x15)) + bytes(ANCS_UUID)   # 0x15: 128 bit service solicitation
    adv = flags + solicit
    resp = bytes((len(name) + 1, 0x09)) + name.encode()   # the name goes in the scan response
    return adv, resp


def text(data):
    """Decodes a value, which iOS may have cut off in the middle of a character."""
    try:
        return data.decode()
    except UnicodeError:
        return str(data)


def parse(data):
    """Reads a Get Notification Attributes reply, or returns None if it is not all here yet.

    The reply is: command (1 byte), notification id (4), then per attribute an id (1), a length
    (2) and that many bytes of text. A long one arrives split over several notifications.
    """
    attributes = {}
    i = 5
    while len(attributes) < 3:
        if len(data) < i + 3:
            return None
        attribute_id = data[i]
        length = struct.unpack_from("<H", data, i + 1)[0]
        if len(data) < i + 3 + length:
            return None
        attributes[attribute_id] = text(data[i + 3:i + 3 + length])
        i += 3 + length
    return attributes


async def fetch(control_point, data_source, uid):
    """Asks the phone for one notification's app, title and message, and waits for them."""
    request = struct.pack("<BIBBHBH", 0, uid, APP, TITLE, title_max, MESSAGE, message_max)
    await control_point.write(request, response=True)

    data = b""
    while True:
        data += await data_source.notified(timeout_ms=5000)
        if data[1:5] != struct.pack("<I", uid):
            data = b""   # a piece of an older reply that timed out; drop it
            continue
        if (attributes := parse(data)) is not None:
            return attributes


async def button_task(control_point):
    """Dismisses the latest notification when the button is pressed."""
    button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
    was_pressed = False
    while True:
        pressed = button.value() == 0
        if pressed and not was_pressed and latest_uid is not None:
            # command 2 is Perform Notification Action, action 1 is negative: dismiss, or
            # decline a call. Action 0 would be positive, answering it.
            await control_point.write(struct.pack("<BIB", 2, latest_uid, 1), response=True)
            print("Dismissed")
        was_pressed = pressed
        await asyncio.sleep_ms(50)


async def listen(connection):
    """Pairs, finds ANCS, and prints every notification until the phone goes away."""
    # ANCS only appears on an encrypted connection. The first time, the iPhone asks whether
    # to pair; after that the saved keys are used and nothing is asked.
    await connection.pair(bond=True)

    ancs = await connection.service(ANCS_UUID)
    if ancs is None:
        print("The phone offered no ANCS. Is it an iPhone?")
        return

    notification_source = await ancs.characteristic(NOTIFICATION_SOURCE_UUID)
    control_point = await ancs.characteristic(CONTROL_POINT_UUID)
    data_source = await ancs.characteristic(DATA_SOURCE_UUID)

    # ponytail: aioble keeps only the last notification by default, and several arrive at
    # once here. Longer queues is a private attribute, so recheck it after updating aioble.
    notification_source._notify_queue = deque((), 32)
    data_source._notify_queue = deque((), 32)

    # data source first, so no reply can arrive before anything is listening for it
    await data_source.subscribe(notify=True)
    await notification_source.subscribe(notify=True)
    print("Listening for notifications")

    button = asyncio.create_task(button_task(control_point)) if button_pin is not None else None
    try:
        await print_notifications(notification_source, control_point, data_source)
    finally:
        # the button belongs to this connection; the next one starts its own
        if button:
            button.cancel()


async def print_notifications(notification_source, control_point, data_source):
    """Fetches and prints each new notification as the phone announces it."""
    global latest_uid
    while True:
        # event, flags, category, count, notification id
        event, flags, category, count, uid = struct.unpack(
            "<BBBBI", await notification_source.notified()
        )
        if event == 2:   # removed
            continue
        if flags & 0x04 and not show_existing:   # already on the phone before we connected
            continue
        attributes = await fetch(control_point, data_source, uid)
        latest_uid = uid
        kind = CATEGORIES[category] if category < len(CATEGORIES) else "Other"
        print()
        print("[%s] %s" % (kind, attributes[APP]))
        print(attributes[TITLE])
        print(attributes[MESSAGE])


async def main():
    adv, resp = advertising_data()
    while True:
        print("Advertising as", name)
        connection = await aioble.advertise(250_000, adv_data=adv, resp_data=resp)
        print("Connected to", connection.device)
        try:
            await listen(connection)
        except (aioble.DeviceDisconnectedError, asyncio.TimeoutError) as error:
            print("Lost the phone:", repr(error))
        await connection.disconnected(timeout_ms=None, disconnect=True)
        print("Disconnected")


asyncio.run(main())
