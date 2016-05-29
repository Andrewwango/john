import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN) #yellow
GPIO.setup(24, GPIO.OUT) #brown

GPIO.output(24, False)
time.sleep(0.1)
GPIO.output(24, True)
time.sleep(0.001)
GPIO.output(24, False)

start = time.time()
stop = time.time()
while GPIO.input(25) == 0:
	start = time.time()
while GPIO.input(25) == 1:
	stop = time.time()
duration = stop - start
distance = duration * 340 * 100 #cm
