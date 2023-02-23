from machine import Pin,PWM

servo=PWM(Pin(17),freq=50, duty=512)

servo.duty(40)
servo.duty(115)
servo.duty(77)