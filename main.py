from BrickPi import *
import time
import RPi.GPIO as GPIO
BrickPiSetup()
GPIO.setmode(GPIO.BCM)

##DEBUG##
#if motors stalling - check voltage + PSU - make sure it's 12V and connections are alright!
#BrickPiUpdateValues error - do system thingy (./stopev.sh)
#if ir is dodgy - check input is 12V
#if result=-1 (of usread) - reboot

##NOTES##
#default position is grabber open, arm fully up
#positive speed = rolling away from bum
#encoder increase = rolling away from bum

'''PROGRAM
 XX- turn x degrees.
- go until edge
- turn -2x degrees and continue, turning -2x degrees each time
- measure degrees using outside wheel
'''

##CONSTANTS##
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1

IRIN = 25 #yellow (when sth close, 0)
USTRIG = 24 #brown, out
USECHO = 23 #green, in

XDEGREES=200

USSTANDARD     = 25 #us sensor threshold
US2STANDARD    = 100
OPTLITTERRANGE = [10,15] #the distance from which it can pick up stuff

WHEELPOWER     = -255
TURNPOWER      = 255
SHOOBYPOWER    = 70

GRABBERPOWER   = -100
OPENPOWER      = 80

LIFTPOWER      = -200
BRINGDOWNPOWER = 100
BRINGDOWNBRAKEPOWER = -5

##SETUP##
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1
BrickPi.MotorEnable[LWHEEL] = 1
BrickPi.MotorEnable[RWHEEL] = 1
GPIO.setup(IRIN, GPIO.IN)
GPIO.setup(USECHO, GPIO.IN)
GPIO.setup(USTRIG, GPIO.OUT)
BrickPi.SensorType[HEAD] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()
turnycount = 0


#############
##FUNCTIONS##
#############
def takeusreading():
	#take 9 readings then find mode
	uslist=[]
	for i in range(9):
		result = BrickPiUpdateValues()
		if not result:
			uslist += [int(BrickPi.Sensor[HEAD])]
		time.sleep(.05)
	print uslist
	usreading = max(set(uslist), key=uslist.count) #mode
	#usreading = sum(uslist)/len(uslist) #mean
	print "usreading is " + str(usreading)
	return usreading
	
def takeus2reading():
	#take 5 readings then find mode
	us2list=[]
	for i in range(5):
		#send out signal
		GPIO.output(USTRIG, False)
		time.sleep(0.1)
		GPIO.output(USTRIG, True)
		time.sleep(0.001)
		GPIO.output(USTRIG, False)
		
		#find length of signal
		start = time.time()
		stop = time.time()
		while GPIO.input(USECHO) == 0:
			start = time.time()
		while GPIO.input(USECHO) == 1:
			stop = time.time()
		duration = stop - start
		
		#find length
		distance = duration * 340 * 100 #cm
		us2list += [int(distance)]
		time.sleep(0.1)
	print us2list
	#us2reading = max(set(us2list), key=us2list.count) #mode
	us2reading = sum(us2list)/len(us2list) #mean
	print "higher us2reading is " + str(us2reading)
	return us2reading

def takeencoderreading(port):
	result = BrickPiUpdateValues()
	if not result :
		print "encoder reading is: " + str((BrickPi.Encoder[port]) /2)
		return ((BrickPi.Encoder[port]) /2)

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower
	BrickPiUpdateValues()

def turnprocedure(thecountvar):
	#turning procedure (param to prevent UnboundLocalError)
	time.sleep(1)
	#check if turn left or right
	if thecountvar%2 == 1: #odd=left
		print "turning left" #use right wheel to encode
		movelimbENC(RWHEEL, -TURNPOWER, XDEGREES*2, LWHEEL, TURNPOWER)
	else:
		print "turning right" #use left wheel to encode
		movelimbENC(LWHEEL, TURNPOWER, XDEGREES*2, RWHEEL, -TURNPOWER)
	drivewheels(0,0)
	thecountvar += 1 #next time turns other way
	time.sleep(0.5)	

def movelimbLENG(limb, speed, length, limb2=None, speed2=None): #movelimb based on time length
	#set speeds
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = speed2
	ot = time.time()
	while(time.time() - ot < length):
		BrickPiUpdateValues()
	time.sleep(.1)
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0

def movelimbENC(limb, speed, encoderdeg, limb2=None, speed2=None): #movelimb based on encoderdeg
	#encoderdeg is the change in encoder degrees
	#positive speed is positive encoder increase
	#i love to wear blue, red and pink dungarees
	startpos = takeencoderreading(limb)
	if speed > 0:
		while takeencoderreading(limb) - startpos < encoderdeg:
			#carry on turning till arm reaches correct pos
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None:
				BrickPi.MotorSpeed[limb2] = speed2
	elif speed < 0:
		while takeencoderreading(limb) - startpos > -encoderdeg:
			#carry on turning till arm reaches correct pos
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None:
				BrickPi.MotorSpeed[limb2] = speed2
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0
		

################
##MAIN PROGRAM##
################
#1. turn x degrees RIGHT to start
#turnprocedure(turnycount)

#main loop
while True:
	#stop actions
	BrickPi.MotorSpeed[GRABBER] = 0
	BrickPi.MotorSpeed[ARM] = 0
	
	#drive
	drivewheels(WHEELPOWER, WHEELPOWER)
	
	#check us for object
	if takeusreading() < USSTANDARD:
		print "object detected"
		drivewheels(0,0)
		
		#activate us2 pos
		print "sliding down bit by bit"
		movelimbENC(ARM, BRINGDOWNPOWER, 50)
		movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
		time.sleep(0.5)


		#check higher us2 for big thing		
		if takeus2reading() > US2STANDARD:
			#LITTER (low-lying object)
			#pick up litter procedure
			print "low-lying object detected"
			time.sleep(1)

			print "shooby" #shooby to get into place
			while takeusreading() > OPTLITTERRANGE[1]: #too far away
				drivewheels(SHOOBYPOWER, SHOOBYPOWER)
			while takeusreading() < OPTLITTERRANGE[0]: #too close
				drivewheels(-SHOOBYPOWER, -SHOOBYPOWER)
			drivewheels(0,0)
		
			print "bringing down" #get grabber into pos
			movelimbLENG(ARM, BRINGDOWNPOWER, 0.7)
			
			#preliminary grab
			movelimbLENG(GRABBER, GRABBERPOWER, 0.5, ARM, BRINGDOWNPOWER)
			
			print "lifting" #bring litter up
			movelimbLENG(ARM, LIFTPOWER, 0.7, GRABBER, GRABBERPOWER) #grabber grips as well

			print "opening" #dump litter
			movelimbLENG(GRABBER, OPENPOWER, 0.5)
			time.sleep(2)
			
		else:
			#WALL
			print "WALL"
			turnprocedure(turnycount)
			
			#bring us2 back up
			print "lifting"
			movelimbLENG(ARM, LIFTPOWER, 0.3)
			#loop back and carry on
	
	#check IR for cliff
	if GPIO.input(IRIN) == 1: #nothing close
		#CLIFF
		print "CLIFF"
		turnprocedure(turnycount)
		#loop back and carry on
