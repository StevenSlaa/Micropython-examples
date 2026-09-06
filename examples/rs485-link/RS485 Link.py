from machine import Pin, UART
from time import sleep, ticks_ms
from rs485 import RS485

# --- Configuration: the same script goes on both boards, with one line different -------------
# "asker" sends a question once a second; "answerer" waits for one and replies. Put this
# script on both boards and change this line on one of them.
role = "asker"

# pins and bus. UART 1 with these pins suits an ESP32; a Pico wants uart_id 0, tx 0, rx 1.
uart_id = 1
tx_pin = 17
rx_pin = 16
de_pin = 4

# Both boards must agree on this. Slower is more forgiving of a long or badly terminated cable.
baudrate = 9600
# ---------------------------------------------------------------------------------------------

uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
bus = RS485(uart, Pin(de_pin), baudrate=baudrate)

print("RS-485 link as the", role, "at", baudrate, "baud")

if role == "asker":
    asked = 0
    answered = 0

    while True:
        asked += 1

        # query() sends and then listens for a reply, which is the shape of nearly every
        # RS-485 system: one board asks, the others only speak when spoken to.
        reply = bus.query(b"time?\n", timeout_ms=300, terminator=b"\n")

        if reply:
            answered += 1
            print("Asked: %d  Answered: %d  Reply: %s" % (asked, answered, reply.strip().decode()))
        else:
            # Nothing came back before the timeout: the other board is off, the pair is swapped,
            # or the two ends disagree about the baud rate.
            print("Asked: %d  Answered: %d  (silence)" % (asked, answered))

        sleep(1)
else:
    replies = 0

    while True:
        if not bus.any():
            continue

        question = bus.readline()
        if not question:
            continue

        replies += 1
        # Only one device may talk at a time, so answering happens strictly after listening.
        # write() holds the line up until the last bit has left, then hands the bus back.
        bus.write(b"%d\n" % ticks_ms())
        print("Replies: %d  Asked: %s" % (replies, question.strip().decode()))
