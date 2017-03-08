import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN)

while True:
	state=GPIO.input(25)
	if state==0:
		print "DETECT"
	elif state==1:
		print "SPACE"
	time.sleep(0.4)
