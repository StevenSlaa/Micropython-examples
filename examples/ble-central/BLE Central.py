# Connecting to a Bluetooth device and reading from it: the other half of the peripheral
# example, doing what a phone app would do.
#
# Run the peripheral example on one board and this on another.

import asyncio
import struct
import aioble
import bluetooth

# --- Configuration ---------------------------------------------------------------------------
# the name the peripheral advertises. Matching on the name rather than the address is
# deliberate: BLE addresses change on purpose, to stop devices being followed around.
target_name = "pulsar-sensor"

# The same UUIDs the peripheral offers. 0x181a is environmental sensing, 0x2a6e temperature.
SERVICE_UUID = bluetooth.UUID(0x181A)
TEMPERATURE_UUID = bluetooth.UUID(0x2A6E)

# how long to look before giving up, in milliseconds
scan_ms = 5000
# ----------------------------------------------------------------------------------------------


def to_celsius(data):
    """0x2a6e is a signed 16 bit number of hundredths of a degree."""
    return struct.unpack("<h", data)[0] / 100


async def find():
    """Scans until the peripheral turns up, or the time runs out."""
    async with aioble.scan(scan_ms, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == target_name and SERVICE_UUID in result.services():
                return result.device
    return None


async def main():
    while True:
        print("Looking for", target_name)
        device = await find()

        if device is None:
            print("Not found; is the peripheral running?")
            continue

        print("Found at", device)

        try:
            # Connecting can fail if the device wandered off between being seen and being
            # called, which happens more often than you would expect.
            connection = await device.connect(timeout_ms=5000)
        except asyncio.TimeoutError:
            print("It stopped answering")
            continue

        async with connection:
            service = await connection.service(SERVICE_UUID)
            characteristic = await service.characteristic(TEMPERATURE_UUID)

            # Reading asks once, which is the simple way.
            print("Read: %.2f C" % to_celsius(await characteristic.read()))

            # Subscribing is the useful way: the peripheral pushes each new value, and nothing
            # is spent asking for a reading that has not changed.
            await characteristic.subscribe(notify=True)
            print("Subscribed; waiting for updates")

            while True:
                data = await characteristic.notified()
                print("Notified: %.2f C" % to_celsius(data))


asyncio.run(main())
