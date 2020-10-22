'''
Hardware test of buttons (touch sensors) used for manual reset.
On running, touch sensor states will be printed continuously.
'''

import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
TOUCHL=4; TOUCHR=11
GPIO.setup(TOUCHL, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TOUCHR, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def taketouchreadings():
	#check if any touch sensor is pressed
	stateL = GPIO.input(TOUCHL); stateR= GPIO.input(TOUCHR)
	if stateL == 0 or stateR == 0: #look for falling edge
		print "touch returns 1"
		return 1
	else: return 0

while True:
	print taketouchreadings()
	time.sleep(0.3)
