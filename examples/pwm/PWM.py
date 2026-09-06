# Written by Steven Slaa

from machine import Pin, PWM
from time import sleep

frequency = 5000 # Frequency in Hertz
led = PWM(Pin(13), frequency)

while True:
  # Increase the duty cycle
  for duty_cycle in range(0, 1024):
    led.duty(duty_cycle)
    # Every 32nd step only: printing all 1024 would flood the console faster than you can
    # read it. In the IDE plotter this draws the triangle wave the LED is following.
    if duty_cycle % 32 == 0:
      print("Duty:", duty_cycle)
    sleep(0.001)
  # Decreasing the duty cycle
  for duty_cycle in reversed(range(0, 1024)):
    led.duty(duty_cycle)
    if duty_cycle % 32 == 0:
      print("Duty:", duty_cycle)
    sleep(0.001)
  # Doing this will create a nice fade effect