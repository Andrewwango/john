import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

TRIG = 17; ECHO=22
DISTANCECUTOFF=200; previoususreading = 100

GPIO.setup(22, GPIO.IN) #yellow, echo
GPIO.setup(17, GPIO.OUT) #purple, trig
GPIO.setup(24, GPIO.OUT) #usother
GPIO.output(24, False); GPIO.output(17, False)

def takeusreading(trig, echo, repeats=3, disregardhigh=False): #take reading from ultrasonic sensor
		global previoususreading
		GPIO.output(trig, False) #switch everything off
		#take 4 readings then find average
		uslist=[]; durationcutoff = DISTANCECUTOFF/34000
		for i in range(repeats):
			distance = 0; duration = 0
			#send out signal
			GPIO.output(trig, False); time.sleep(0.001)
			GPIO.output(trig, True);  time.sleep(0.001)
			GPIO.output(trig, False)
			
			#find length of signal
			start = time.time(); stop = time.time()
			while GPIO.input(echo) == 0:
				start = time.time()
			#	print "start"
			#	if (start-stop) >= 0.006:
			#		distance = DISTANCECUTOFF
			#		break #bail out if waiting too long
			while GPIO.input(echo) == 1:
				stop  = time.time()
			#	print "stop"
			#	if (stop-start) >= 0.006:
			#		distance = DISTANCECUTOFF
			#		break #bail out if waiting too long
			#breaks when cut off point is bypassed - this prevents stalling.
			
			duration = abs(stop - start)
			

			#find length
			if distance == 0: distance = duration * 340 * 100 #cm from speed of sound
			if disregardhigh == True:
				if int(distance) >= DISTANCECUTOFF:
					print "not adding"
					continue #don't add it
			uslist += [int(distance)]
			time.sleep(0.01)
		if uslist == []: uslist.append(previoususreading) #juuust in case everything was disregarded
		uslist.sort(); usreading = uslist[len(uslist)/2] #median (get rid of anomalies)
		previoususreading = usreading
		GPIO.output(trig, False)
		print "US reading is ", str(usreading), uslist
		return usreading


while True:
	try:
		takeusreading(TRIG,ECHO,repeats=3)
		time.sleep(0.5)
	except KeyboardInterrupt:
		GPIO.cleanup()



