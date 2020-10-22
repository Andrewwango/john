'''
Hardware test of IR pavement cliff sensor.
On running, "DETECTED" or "NOT DETECTED" will be printed if there is an object in front of the IR
sensor, according to the hardware op-amp threshold.
'''

import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN)

while True:
	state=GPIO.input(25)
	if state==0:
		print "DETECTED"
	elif state==1:
		print "NOT DETECTED"
	time.sleep(0.4)
