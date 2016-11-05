import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN)

while True:
	state=GPIO.input(25)
	if state==0:
		print "0"
	elif state==1:
		print "11111111111111111111111111111111111111111111111111111111111111111111111111"
	time.sleep(0.2)
