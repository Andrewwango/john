import time
import RPi.GPIO as GPIO
from BrickPi import *
from toplevelconstants import *
GPIO.setmode(GPIO.BCM)

def takeusreading(trig, echo): #detect distance of a us
	GPIO.output(trig, False) #switch everything off
	#take 5 readings then find average
	uslist=[]
	for i in range(3):
		#send out signal
		GPIO.output(trig, False)
		time.sleep(0.001)
		GPIO.output(trig, True)
		time.sleep(0.001)
		GPIO.output(trig, False)
		
		#find length of signal
		start = time.time()
		stop = time.time()
		while GPIO.input(echo) == 0:
			start = time.time()
		while GPIO.input(echo) == 1:
			stop = time.time()
		duration = stop - start
		
		#find length
		distance = duration * 340 * 100 #cm
		uslist += [int(distance)]
		time.sleep(0.01)
	uslist.sort(); usreading = uslist[1] #median (get rid of anomalies)
	GPIO.output(trig, False)
	print "US reading is ", str(usreading), uslist
	return usreading

def taketouchreadings():
	#check if any touch sensor is pressed
	result = BrickPiUpdateValues()
	if not result:
		if BrickPi.Sensor[TOUCHL]==1 or BrickPi.Sensor[TOUCHR]==1:
			print "TOUCH"; return 1
		else:
			return 0
def takeencoderreading(port): #read motor position
	for i in range(3): #deal with encoder glitches
		result = BrickPiUpdateValues()
		if not result :
			return (BrickPi.Encoder[port])
	return 0 #better than nonetype

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower
	BrickPiUpdateValues()
