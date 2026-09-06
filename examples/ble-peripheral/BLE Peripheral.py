# Being a Bluetooth device that a phone, or another board, can connect to and read from.
#
# This advertises a temperature service, lets whatever connects read the value, and pushes a
# new one to anything that subscribed. It is exactly the shape of a real BLE sensor.

import asyncio
import struct
from random import uniform
import aioble
import bluetooth

# --- Configuration ---------------------------------------------------------------------------
# the name that appears when something scans for devices
name = "pulsar-sensor"

# Short UUIDs are registered standard meanings that any app already understands: 0x181a is
# environmental sensing and 0x2a6e is temperature, in hundredths of a degree. Using them means
# a generic phone app shows a temperature rather than four unexplained bytes.
SERVICE_UUID = bluetooth.UUID(0x181A)
TEMPERATURE_UUID = bluetooth.UUID(0x2A6E)

# how often to publish a new reading, in seconds
interval = 2

# how often to advertise, in microseconds. Longer is less power and slower to be discovered.
advertising_interval_us = 250_000
# ----------------------------------------------------------------------------------------------

# A service holds characteristics; a characteristic is one value with a name. read lets a
# central ask for it, notify lets us push it without being asked.
service = aioble.Service(SERVICE_UUID)
temperature_characteristic = aioble.Characteristic(
    service, TEMPERATURE_UUID, read=True, notify=True
)
# Registering has to happen before advertising, and only once.
aioble.register_services(service)


def publish(celsius):
    """Writes the value into the characteristic, in the units the standard UUID expects."""
    # 0x2a6e is a signed 16 bit number of hundredths of a degree, so 21.5C is 2150. Getting
    # this wrong is why a phone app sometimes shows a temperature of 8000 degrees.
    temperature_characteristic.write(struct.pack("<h", int(celsius * 100)), send_update=True)


async def sensor_task():
    """Publishes a reading every few seconds, connected or not."""
    while True:
        # A real one would be a sensor. Any of the Sensors examples drops straight in here.
        celsius = uniform(20.0, 25.0)
        publish(celsius)
        print("Temperature: %.2f C" % celsius)
        await asyncio.sleep(interval)


async def advertise_task():
    """Advertises, waits for a connection, and starts advertising again when it ends."""
    while True:
        print("Advertising as", name)
        # This waits until something connects, and hands back the connection.
        connection = await aioble.advertise(
            advertising_interval_us,
            name=name,
            services=[SERVICE_UUID],
            appearance=0x0300,  # generic thermometer, which decides the icon some apps show
        )
        print("Connected to", connection.device)

        # Nothing else to do while connected: the sensor task keeps publishing, and anything
        # subscribed receives it.
        await connection.disconnected()
        print("Disconnected")


async def main():
    # Both run at once, which is the point of doing this with asyncio.
    await asyncio.gather(sensor_task(), advertise_task())


asyncio.run(main())
