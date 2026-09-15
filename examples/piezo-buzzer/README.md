---
example: piezo-buzzer
author: Steven Slaa
---

# Piezo Buzzer

In this example the microcontroller makes sound with a piezo buzzer: two short beeps, a melody,
and a siren that slides up and down, over and over.

A piezo buzzer is a thin ceramic disc that bends when it gets a voltage. Switch that voltage on
and off hundreds or thousands of times a second and it vibrates, and you hear a tone. The
[driver README](../../drivers/piezo) explains more.

## Requires
This example needs the [Piezo buzzer](../../drivers/piezo) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Passive or active?

Set `active` at the top of the script to match your buzzer. The two look the same from the top.

- **Passive** (`active = False`): you can see a green circuit board underneath. It plays any
  pitch, so you hear the melody.
- **Active** (`active = True`): sealed with black filling underneath, and often a sticker on
  top. It has its own oscillator and beeps at one pitch, so the melody comes out as a rhythm and
  the siren as one long beep.

Not sure? Hold it across a 3V coin cell or the board's 3V3 and GND for a moment. A continuous
beep is active, a single click is passive.

## Connections

| Buzzer | ESP32 | Pico |
| --- | --- | --- |
| + (longer leg, or red wire) | 18 | 18 |
| − | GND | GND |

A small piezo buzzer draws only a few milliamps and can go straight on a pin. A 100Ω resistor in
series with the + leg is cheap insurance for the pin.

A **magnetic** buzzer looks just like a piezo one but has a coil inside, draws 30mA or more, and
needs a transistor and a diode between it and the pin. If yours measures a few tens of ohms
across its legs with a multimeter, it is magnetic.

## Output
```
Frequency: 2000 Hz
Frequency: 0 Hz
Melody
Frequency: 600 Hz
Frequency: 620 Hz
Frequency: 640 Hz
...
Frequency: 0 Hz
```

## Writing your own melody

Change the `melody` string. Notes are separated by spaces: `C5` is the note C in octave 5, `F#5`
and `Bb5` are sharps and flats, `A5:2` lasts two beats, `A5:0.5` half a beat, and `R` is a
rest. `tempo` is how many beats there are per minute.

```python
melody = "E5:0.5 D#5:0.5 E5:0.5 D#5:0.5 E5:0.5 B4:0.5 D5:0.5 C5:0.5 A4:2"   # Für Elise
```

Small buzzers are loudest between about 2kHz and 4kHz, so a tune in octave 5 or 6 sounds much
louder than one in octave 4.

## Plotter

Open the **Plotter** tab beside the REPL to graph the frequency. The two beeps show as one short
spike, and the siren draws a triangle as the pitch climbs to 1800Hz
and falls back. The melody prints no numbers, so the plot pauses while it plays.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
