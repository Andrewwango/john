import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO.setup(7, GPIO.OUT)

GPIO.output(7, True)
time.sleep(0.1)
GPIO.output(7,False)

GPIO.cleanup()
