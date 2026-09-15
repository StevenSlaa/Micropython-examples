# Driver for piezo buzzers: beeps, tones and melodies.
#
# There are two kinds, and they look the same from the top:
#
#   passive    a bare piezo element. It makes no sound of its own, so it is fed a square wave
#              with PWM and plays whatever pitch it is given. Also bare piezo discs.
#   active     has its own oscillator inside. Give it power and it beeps at one fixed pitch, so
#              it is switched on and off like an LED. Pass active=True.
#
# Every sound is stopped in a `finally`, so a melody interrupted with Ctrl+C, or an exception
# halfway through, does not leave the buzzer screaming.

from time import sleep_ms

_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_frequency(name):
    """The frequency in Hz of a note name like "A4", "C#5" or "Bb3". A bare letter is octave 4."""
    try:
        semitone = _SEMITONES[name[0].upper()]
        rest = name[1:]
        if rest[:1] == "#":
            semitone += 1
            rest = rest[1:]
        elif rest[:1] == "b":
            semitone -= 1
            rest = rest[1:]
        octave = int(rest) if rest else 4
    except (KeyError, IndexError, ValueError):
        raise ValueError("Not a note: %r" % name)
    # Equal temperament around A4 = 440Hz, counted in MIDI note numbers.
    return round(440 * 2 ** ((12 * (octave + 1) + semitone - 69) / 12))


def _parse(melody):
    """[(frequency, beats), ...] from "C5 E5:0.5 R G5:2". A frequency of 0 is a rest."""
    notes = []
    for token in melody.split():
        name, _, beats = token.partition(":")
        try:
            beats = float(beats) if beats else 1.0
        except ValueError:
            beats = 0
        if beats <= 0:
            raise ValueError("Not a length: %r" % token)
        notes.append((0 if name.upper() == "R" else note_frequency(name), beats))
    return notes


class Piezo:
    """A piezo buzzer on `pin`.

    `volume` runs 0.0 to 1.0 and only works on a passive buzzer. `gap_ms` is the silence left at
    the end of every note in a melody, so two of the same note in a row are heard as two.
    """

    def __init__(self, pin, active=False, volume=1.0, gap_ms=20):
        self.active = active
        self.volume = volume
        self.gap_ms = gap_ms
        if active:
            pin.init(pin.OUT, value=0)
            self._pin = pin
        else:
            from machine import PWM

            # Created silent. A PWM made without a duty starts at 50% on some ports, a click.
            self._pwm = PWM(pin, freq=1000, duty_u16=0)

    def _sound(self, frequency):
        if self.active:
            self._pin.value(1 if frequency else 0)
        elif frequency and self.volume > 0:
            self._pwm.freq(int(frequency))
            # A 50% square wave is as loud as a piezo gets; a narrower pulse is quieter.
            self._pwm.duty_u16(int(32768 * min(self.volume, 1.0)))
        else:
            self._pwm.duty_u16(0)

    def stop(self):
        """Silence."""
        self._sound(0)

    def tone(self, frequency=2000, duration_ms=None):
        """Sounds `frequency` Hz for `duration_ms`, or until stop() when no duration is given.

        An active buzzer ignores the frequency and sounds its own.
        """
        if duration_ms is None:
            self._sound(frequency)
            return
        try:
            self._sound(frequency)
            sleep_ms(duration_ms)
        finally:
            self.stop()

    def play(self, melody, tempo=120):
        """Plays a melody string and returns when it is done.

        Notes are separated by spaces: a name and octave, then optionally a colon and a length in
        beats, which defaults to 1. `R` is a rest. `tempo` is beats per minute.

            piezo.play("C5 C5 G5 G5 A5 A5 G5:2")
        """
        # All of it first, so a typo is an error before the tune starts rather than halfway in.
        notes = _parse(melody)
        beat_ms = 60000 / tempo
        try:
            for frequency, beats in notes:
                duration = int(beats * beat_ms)
                if frequency:
                    gap = min(self.gap_ms, duration // 2)
                    self._sound(frequency)
                    sleep_ms(duration - gap)
                    self.stop()
                    sleep_ms(gap)
                else:
                    sleep_ms(duration)
        finally:
            self.stop()
