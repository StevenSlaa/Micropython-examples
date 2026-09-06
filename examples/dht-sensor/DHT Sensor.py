# Written by Steven Slaa

from machine import Pin
from time import sleep
import dht 

sensor = dht.DHT11(Pin(15))
#sensor = dht.DHT22(Pin(15))

while True:
  try:
    sleep(2)
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    temp_f = temp * (9/5) + 32.0
    # One line per reading, with a name for each value: the IDE plotter draws a series per
    # name, so two lines both called Temperature would land in the same one.
    print('Temperature: %3.1f C  Fahrenheit: %3.1f F  Humidity: %3.1f %%' % (temp, temp_f, hum))
  except OSError as e:
    print('Failed to read sensor.')