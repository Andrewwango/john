from BrickPi import *
import time
import RPi.GPIO as GPIO
BrickPiSetup()
GPIO.setmode(GPIO.BCM)

##DEBUG##
#if motors stalling - check voltage + PSU
#BrickPiUpdateValues error - do system thingy (./stopev.sh)
#if result=-1 - reboot

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

WHEELPOWER     = -200
TURNPOWER      = 200

GRABBERPOWER   = -100
OPENPOWER      = 80

LIFTPOWER      = -200
BRINGDOWNPOWER = 200

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
def movelimb(limb, speed, length, limb2=None, speed2=None):
	#set speeds
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = speed2
	ot = time.time()
	while(time.time() - ot < length):
		BrickPiUpdateValues()
	time.sleep(.1)

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

def turnwheels(direction, encoderdeg):
	if direction == "right":
		startpos = takeencoderreading(LWHEEL)
		while takeencoderreading(LWHEEL) - startpos < encoderdeg:
			#carry on turning right till left wheel reaches correct pos
			drivewheels(TURNPOWER,-TURNPOWER)
	elif direction == "left":
		startpos = takeencoderreading(RWHEEL)
		while takeencoderreading(RWHEEL) - startpos < encoderdeg:
			#carry on turning left till right wheel reaches correct pos
			drivewheels(-TURNPOWER,TURNPOWER)
	drivewheels(0,0)

def turnprocedure():
	#turning procedure
	time.sleep(1)
	#check if turn left or right
	if turnycount%2 == 1: #odd=left
		print "turning left"
		turnwheels("left", XDEGREES*2)
	else:
		print "turning right"
		turnwheels("right",XDEGREES*2)
	turnycount += 1 #next time turns other way
	time.sleep(0.5)	

################
##MAIN PROGRAM##
################
#1. turn x degrees RIGHT to start
#print "turning"
#turnwheels("right", XDEGREES)
#turnycount = 1 #odd=needs to turn left on next turn

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
		startpos = takeencoderreading(ARM)
		while takeencoderreading(ARM) - startpos < 60:
			#carry on turning till arm reaches correct pos
			BrickPi.MotorSpeed[ARM] = 40
		BrickPi.MotorSpeed[ARM] = 0
		time.sleep(0.5)

		#check higher us2 for big thing		
		if takeus2reading() > US2STANDARD:
			#LITTER (low-lying object)
			#pick up litter procedure
			print "low-lying object detected"
			time.sleep(1)

			print "shooby" #shooby forwards to get into place
			movelimb(LWHEEL,  WHEELPOWER, 0.3, RWHEEL,  WHEELPOWER)
			drivewheels(0,0)
		
			print "bringing down" #get grabber into pos
			movelimb(ARM, BRINGDOWNPOWER, 0.5)
			time.sleep(0.2)

			#preliminary grab
			movelimb(GRABBER, GRABBERPOWER, 0.4)
			
			print "lifting" #bring litter up
			movelimb(ARM, LIFTPOWER, 0.7, GRABBER, GRABBERPOWER) #grabber grips as well

			print "opening" #dump litter
			movelimb(GRABBER, OPENPOWER, 0.5)
			time.sleep(2)
			
		else:
			#WALL
			print "WALL"
			turnprocedure()
			
			#bring arm back up
			print "lifting"
			movelimb(ARM, LIFTPOWER, 0.3)
			#loop back and carry on
	
	#check IR for cliff
	if GPIO.input(IRIN) == 1: #nothing close
		#CLIFF
		print "CLIFF"
		turnprocedure()
		#loop back and carry on
