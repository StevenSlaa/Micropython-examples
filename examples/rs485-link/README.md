# RS-485 Link (MAX485)

In this example two boards talk to each other over RS-485: one asks a question every second and
the other answers.

**The same script goes on both boards.** Change `role` at the top of one of them to
`"answerer"`, and leave the other as `"asker"`.

Unlike a plain UART between two boards, this keeps working down a long cable — hundreds of
metres of it, through a building full of electrical noise — because each bit is carried as the
difference between two wires rather than against ground.

## Requires
This example needs the [RS-485 (MAX485)](../../drivers/rs485) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Each board gets its own transceiver module, and the two modules are joined by the pair.

| Module | ESP32 | Pico |
| --- | --- | --- |
| DI | 17 (UART TX) | 0 |
| RO | 16 (UART RX) | 1 |
| DE and RE, tied together | 4 | 2 |
| VCC | 5V | VBUS (5V) |
| GND | GND | GND |

On a Pico also set `uart_id = 0` at the top of the script.

Between the two modules:

```
   board A                     board B
  ┌────────┐                 ┌────────┐
  │  A ────┼─────────────────┼──── A  │
  │  B ────┼─────────────────┼──── B  │
  │ GND ───┼─────────────────┼─── GND │
  └────────┘                 └────────┘
     120Ω across A and B at each end
```

Use a twisted pair for A and B — one pair out of an ethernet cable is ideal. Join the grounds
too: RS-485 tolerates some difference between them, but not an unlimited one.

**Termination** is a 120Ω resistor across A and B at each *end* of the run, and nowhere in
between. Many breakout boards have one fitted already, which is right for two boards. On a
short cable on a desk it all works without any of this, which is exactly why the problem turns
up later, on the long run, rather than now.

## Output

On the asking board:

```
RS-485 link as the asker at 9600 baud
Asked: 1  Answered: 1  Reply: 5312
Asked: 2  Answered: 2  Reply: 6318
Asked: 3  Answered: 2  (silence)
```

On the answering board:

```
RS-485 link as the answerer at 9600 baud
Replies: 1  Asked: time?
Replies: 2  Asked: time?
```

The number in the reply is the answering board's own uptime in milliseconds — proof that the
answer really came from the other board rather than from anything local.

## One at a time

RS-485 has a single pair of wires, so only one device may talk at a time and each has to say
which it is doing. Nothing arbitrates that for you: if both boards transmit at once, both
messages are destroyed.

That is why this example has one asker and one answerer, and why real systems are built the
same way — one board asks, and the others speak only when spoken to. Adding a third board is
just another answerer, given a different question to respond to.

## If they cannot hear each other

| What you see | What to try |
| --- | --- |
| `(silence)` every time | Swap A and B. Manufacturers disagree about which is which, and this is by far the most common cause |
| Rubbish in the replies | The two boards disagree on `baudrate` |
| The end of each message missing | Check `baudrate` is the same in `UART(...)` and `RS485(...)`: the driver uses it to know when a send has finished |
| Works on a short wire, not a long one | Termination, or the grounds are not joined |
| Nothing on either board | Are DE and RE tied together and on the pin in the config? |

## Plotter

Open the **Plotter** tab beside the REPL on the asking board to graph asked against answered.
The gap between the two lines is how many exchanges went missing, which is a good way to judge a
cable or a termination change: make one, and watch whether the lines stay together.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
