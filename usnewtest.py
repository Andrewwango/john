import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

GPIO.setup(22, GPIO.IN) #yellow, echo
GPIO.setup(17, GPIO.OUT) #purple, trig
GPIO.setup(24, GPIO.OUT) #brown, trig
GPIO.output(24, False); GPIO.output(17, False)

while True:
	GPIO.output(17, False)
	time.sleep(0.1)
	GPIO.output(17, True)
	time.sleep(0.001)
	GPIO.output(17, False)
	
	start = time.time()
	stop = time.time()
	while GPIO.input(22) == 0:
		start = time.time()
	while GPIO.input(22) == 1:
		stop = time.time()
	duration = stop - start
	distance = int(duration * 340 * 100) #cm
	print distance
	time.sleep(0.5)
