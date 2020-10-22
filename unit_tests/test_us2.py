'''
Hardware test of custom Ultrasonic sensors.
On running, US sensor output will be printed continuously.
'''

import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

GPIO.setup(23, GPIO.IN) #green, echo
GPIO.setup(24, GPIO.OUT) #brown, trig
GPIO.setup(17, GPIO.OUT)
GPIO.output(24, False); GPIO.output(17, False)

while True:
	try:
		GPIO.output(24, False)
		time.sleep(0.1)
		GPIO.output(24, True)
		time.sleep(0.001)
		GPIO.output(24, False)

		start = time.time()
		stop = time.time()
		while GPIO.input(23) == 0:
			start = time.time()
		while GPIO.input(23) == 1:
			stop = time.time()
		duration = stop - start
		distance = int(duration * 340 * 100) #cm
		print distance
		time.sleep(0.5)
	except KeyboardInterrupt:
		GPIO.cleanup()
