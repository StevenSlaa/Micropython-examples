from machine import Pin
from time import sleep, sleep_ms
from piezo import Piezo

# Configuration
# the pin the buzzer's + leg is on
piezo_pin = 18
# False for a passive buzzer or a bare piezo disc, which plays any pitch.
# True for an active buzzer, which beeps at its own pitch, so melodies become just their rhythm.
active = False
# 0.0 to 1.0, passive buzzers only
volume = 1.0

piezo = Piezo(Pin(piezo_pin), active=active, volume=volume)

# Twinkle Twinkle Little Star. A note name and octave, and after the colon how many beats.
melody = "C5 C5 G5 G5 A5 A5 G5:2 F5 F5 E5 E5 D5 D5 C5:2"

while True:
    # Two short beeps.
    print("Frequency: 2000 Hz")
    piezo.tone(2000, 100)
    sleep_ms(100)
    piezo.tone(2000, 100)
    print("Frequency: 0 Hz")
    sleep(1)

    print("Melody")
    piezo.play(melody, tempo=160)
    sleep(1)

    # A siren: one tone that keeps sounding while its pitch slides up and down.
    for frequency in list(range(600, 1800, 20)) + list(range(1800, 600, -20)):
        print("Frequency: %d Hz" % frequency)
        piezo.tone(frequency)
        sleep_ms(15)
    piezo.stop()
    print("Frequency: 0 Hz")
    sleep(1)
