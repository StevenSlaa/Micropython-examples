# Analog Read (potentiometer)

A digital pin answers one question: *is there a voltage on this wire?* Yes or no, on or off.

Plenty of the world does not fit into that. How far is the knob turned, how bright is the room,
how wet is the soil, how full is the battery — all of those are questions about *how much*, and
answering them is what an analog input is for.

The good news is that they are all the same three lines of code.

## What you will learn

- What the number from an analog pin actually represents
- How to turn that number into volts, or a percentage, or anything else you need
- Which pins you can use, and the one that will waste your afternoon if you pick wrong

## Wire it up

A potentiometer — a knob — is the easiest thing to start with. Any value from 1kΩ to 100kΩ will
do; they are all the same for this.

It has three legs. The two outer ones go to 3.3V and GND, and it does not matter which way
round: that only decides which way you turn it to get a bigger number. The middle leg is the
interesting one. Inside, it is a contact sliding along a strip of resistive material between the
two ends, so its voltage is wherever you have turned it to.

```
3.3V ───\/\/\/\/\/\─── GND
              │
            wiper ───── GPIO 34
```

| | ESP32 | Pico |
| --- | --- | --- |
| Wiper (middle leg) | 34 | 26 |
| Outer legs | 3V3 and GND | 3V3 and GND |

**On an ESP32, use a pin between 32 and 39.** Those belong to the converter called ADC1. The
rest of the analog pins are on ADC2, which stops working as soon as wifi is switched on, with no
error and no warning — the readings simply stop changing. It is a genuinely nasty one to debug,
and picking the right pin avoids it entirely.

No potentiometer? A light dependent resistor and a fixed resistor of about 10kΩ, in series
between 3.3V and GND with the pin on the join, works exactly the same way and follows the light
in the room.

## Run it

Turn the knob slowly and watch the numbers.

```
Raw:     0  Volts: 0.00  Percent: 0.0
Raw: 32741  Volts: 1.65  Percent: 50.0
Raw: 65535  Volts: 3.30  Percent: 100.0
```

## How it works

Inside the board is an analog to digital converter — an ADC. It compares the voltage on the pin
against the board's own supply and reports where between the two it sits:

| The pin is at | `read_u16()` gives | Which is |
| --- | --- | --- |
| 0V | about 0 | nothing |
| 1.65V | about 32768 | half way |
| 3.3V | about 65535 | as far as it goes |

```python
raw = adc.read_u16()
```

That number is always 0 to 65535, on every board. Underneath, most of these chips actually
measure in 4096 steps rather than 65536, and the result is scaled up to fit — which is why the
last few digits jump around instead of counting smoothly. That jitter is normal. If it bothers
you, read five times and take the average.

```python
volts = raw / 65535 * reference_volts
percent = raw / 65535 * 100
```

Here is the part worth remembering, because you will use it constantly. Divide by the largest
the reading can be, and you have a fraction from 0 to 1 — a plain "how far along is it". Then
multiply by whatever unit you want to talk in. Volts, percent, degrees, millimetres: the second
number is the only thing that changes.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| The number never changes | On an ESP32, an ADC2 pin with wifi on. Move to a pin between 32 and 39 |
| It jumps about with nothing connected | Normal. An unconnected analog pin is a small aerial, not a zero |
| It stops at about 45000 instead of 65535 | The `adc.atten` line did not run. Without it an ESP32 only measures the bottom of the range |
| It never quite reaches 0 or 65535 | Also normal on an ESP32; the converter is not very truthful in the last tenth of a volt at each end |
| Nothing but 0, or nothing but 65535 | The wiper is not connected, or the outer legs are not on 3.3V and GND |
| An error mentioning ADC | Wrong pin: not every pin can measure |

## Plotter

This is where the plotter earns its place. Open the **Plotter** tab beside the REPL and turn the
knob slowly from one end to the other.

A column of numbers tells you the value. The line tells you the *behaviour*: the jitter in the
last digits, the flat spot at each end where a cheap potentiometer stops changing before it
stops turning, and the sudden spikes if a wire is loose. None of that is visible any other way,
and all of it matters when you are trying to work out why a reading is not what you expected.

## Try changing

- **Average five readings** before printing, and watch the jitter disappear:
  ```python
  raw = sum(adc.read_u16() for _ in range(5)) // 5
  ```
- **Print only when it moves**, by remembering the last value and comparing. Most sensors are
  read far more often than they change.
- **Swap the knob for a light sensor**, and put your hand over it. The numbers are the same
  kind of thing; only what they mean has changed.

## Things worth knowing

- Never put more than 3.3V on an analog pin. To measure a 9V battery, two resistors first divide
  it down; connecting it directly damages the pin.
- The reading is relative to the board's supply, not to anything absolute. On battery power, as
  the supply sags, a steady voltage will appear to rise.

## Next

[Analog Read and Write](../dimmer) uses this reading to control something, which is
where inputs start being useful.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.

---

**The five basics:** [1. Blink](../blink) · [2. Button](../button) · [4. PWM](../pwm) · [5. Dimmer](../dimmer)
