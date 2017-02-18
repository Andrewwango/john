import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
	state=GPIO.input(11)
	if state==0:
		print "11111111111111111111111111111111111111111111111"
	elif state==1:
		print "1"
	state2=GPIO.input(4)
 	if state2==0:
		print "222222222222222222222222222222222222222222222"
	elif state2==1:
		print "2"
		
	time.sleep(0.2)
