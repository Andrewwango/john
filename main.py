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

##CONSTANTS##
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1

IRIN = 25 #yellow (when sth close, 0)
USTRIG = 24 #brown, out
USECHO = 23 #green, in

USSTANDARD     = 25 #us sensor threshold
US2STANDARD    = 100

WHEELPOWER     = -100
TURNPOWER      = -255

GRABBERPOWER   = -100
OPENPOWER      = 40

LIFTPOWER      = -230
BRINGDOWNPOWER = 100

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
	us2reading = max(set(us2list), key=us2list.count) #mode
	print "higher us2reading is " + str(us2reading)
	return us2reading

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower	

#############
##MAIN LOOP##
#############
while True:
	#stop actions
	BrickPi.MotorSpeed[GRABBER] = 0
	BrickPi.MotorSpeed[ARM] = 0
	
	#drive
	drivewheels(WHEELPOWER, WHEELPOWER)
	
	#check us for object
	if takeusreading() < USSTANDARD:
		print "object detected"
		
		#check higher us2 for big thing
		print "sliding down" #activate us2 pos
		movelimb(ARM, BRINGDOWNPOWER, 0.1)
		
		if takeus2reading() > US2STANDARD:
			#low-lying object - pick up litter procedure
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
			#wall
			print "wall: sliding up" #get back into normal pos
			movelimb(ARM, LIFTPOWER, 0.1)
			time.sleep(1)
			
			#reverse, turn right, go, then turn right again
			movelimb(LWHEEL, -WHEELPOWER, 0.4, RWHEEL, -WHEELPOWER)
			movelimb(LWHEEL,  TURNPOWER, 2, RWHEEL, -TURNPOWER)			
			movelimb(LWHEEL,  WHEELPOWER, 0.4, RWHEEL,  WHEELPOWER)
			movelimb(LWHEEL,  TURNPOWER, 2, RWHEEL, -TURNPOWER)
			drivewheels(0,0)
	
	#check IR for cliff
	if GPIO.input(IRIN) == 1: #nothing close
		pass
