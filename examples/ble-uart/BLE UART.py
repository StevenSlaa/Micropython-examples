# A serial port over Bluetooth: type a command on a phone, the board answers.
#
# This is the Nordic UART Service, which is not an official standard but is so widely copied
# that every BLE terminal app speaks it. One characteristic carries text from the phone to the
# board, another carries it back.

import asyncio
from machine import Pin
import aioble
import bluetooth

# --- Configuration ---------------------------------------------------------------------------
# the name that appears when the phone scans
name = "pulsar-uart"

# the led the commands switch. GPIO 2 is the onboard led on most ESP32 boards; on a Pico W
# use "LED".
led = Pin(2, Pin.OUT)
# ----------------------------------------------------------------------------------------------

# The UUIDs Nordic picked. RX and TX are named from the board's side: the board receives on
# RX and transmits on TX, which is backwards from how the phone app labels them.
UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

service = aioble.Service(UART_UUID)
# capture keeps every write in a queue, so two quick commands do not become one
rx = aioble.Characteristic(service, RX_UUID, write=True, write_no_response=True, capture=True)
tx = aioble.Characteristic(service, TX_UUID, notify=True)
aioble.register_services(service)


def send(connection, message):
    """Sends text to the phone, 20 bytes at a time: the most one packet holds by default."""
    data = (message + "\n").encode()
    for i in range(0, len(data), 20):
        tx.notify(connection, data[i:i + 20])


def handle(command):
    """Turns one command into a reply. Add your own here."""
    if command == "on":
        led.on()
        return "led is on"
    if command == "off":
        led.off()
        return "led is off"
    if command == "status":
        return "led is " + ("on" if led.value() else "off")
    return "unknown command, try: on, off, status"


async def main():
    while True:
        print("Advertising as", name)
        connection = await aioble.advertise(250_000, name=name, services=[UART_UUID])
        print("Connected to", connection.device)
        send(connection, "hello, try: on, off, status")

        while connection.is_connected():
            try:
                _, data = await rx.written(timeout_ms=1000)
            except asyncio.TimeoutError:
                continue   # only here to notice a disconnect
            # ponytail: one write is one command. A terminal app sends a line per write;
            # buffer until "\n" if you send commands longer than 20 bytes.
            try:
                command = data.decode().strip().lower()
            except UnicodeError:
                continue   # not text; anything can write to a characteristic
            print(">", command)
            reply = handle(command)
            print("<", reply)
            send(connection, reply)

        print("Disconnected")


asyncio.run(main())
