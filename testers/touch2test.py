import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(11, GPIO.IN)
GPIO.setup(4, GPIO.IN)

while True:
	state=GPIO.input(11)
	if state==0:
		print "0"
	elif state==1:
		print "1111111111111111111111111111111111"
	state2=GPIO.input(4)
 	if state==0:
		print "0"
	elif state==1:
		print "222222222222222222222222222222222"
   
	time.sleep(0.2)
