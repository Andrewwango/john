import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN)

while True:
  print GPIO.input(25)
  time.sleep(0.2)
