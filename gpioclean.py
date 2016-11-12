import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

GPIO.setup(22, GPIO.IN)
GPIO.setup(23, GPIO.IN)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

time.sleep(1)
GPIO.cleanup()
