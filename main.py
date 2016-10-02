####TURNING PROGRAMMING
####best collection of data from us and us2 (mode/mean/repeats)
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
#if cliff sensor dodgy - check connections

##NOTES##
#default position is grabber open, arm fully up
#positive speed = rolling away from bum
#encoder increase = rolling away from bum

'''PROGRAM
- start facing 90o right
- turn x degrees left
- go until edge
- turn 2x degrees and continue, turning 2x degrees each time
- measure degrees using outside wheel
'''

##CONSTANTS##
#Port Assignments
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1

#GPIO Pins
IRIN = 25 #yellow (when sth close, 0)
USTRIG = 24 #brown, out
USECHO = 23 #green, in

XDEGREES=200 #angle between robot path and normal to edge, measured by outside wheel (in encoderdegs)

USSTANDARD     = 25 #us sensor detection threshold
US2STANDARD    = 100 #higher us(2) detection threshold
OPTLITTERRANGE = [10,15] #the opt distance range from which it can pick up stuff

WHEELPOWER     = -255
TURNPOWER      = 255
SHOOBYPOWER    = -100
GRABBERPOWER   = -100
OPENPOWER      = 80
LIFTPOWER      = -200
BRINGDOWNPOWER = 100
BRINGDOWNBRAKEPOWER = -5

##SETUP## motors, sensors, GPIO Pins
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
def takeusreading(): #detect distance of us
	#take 9 readings then find average
	uslist=[]
	for i in range(9):
		result = BrickPiUpdateValues()
		if not result:
			uslist += [int(BrickPi.Sensor[HEAD])]
		time.sleep(.02)
	print uslist
	usreading = max(set(uslist), key=uslist.count) #mode (removes anomalies)
	#usreading = sum(uslist)/len(uslist) #mean
	print "usreading is " + str(usreading)
	return usreading
	
def takeus2reading(): #detect distance of us2
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
	us2list.sort()
	print us2list
	#us2reading = max(set(us2list), key=us2list.count) #mode
	#us2reading = sum(us2list)/len(us2list) #mean
	us2reading = us2list[2] #median
	print "higher us2reading is " + str(us2reading)
	return us2reading

def takeencoderreading(port): #read motor position
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
	thecountvar += 1 #next time turns other way
	time.sleep(0.5)	

def movelimbLENG(limb, speed, length, limb2=None, speed2=None): #move motor based on time length
	#set speeds
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None: #optional simultaneous second motor movement
		BrickPi.MotorSpeed[limb2] = speed2
	ot = time.time()
	while(time.time() - ot < length):
		BrickPiUpdateValues()
	time.sleep(.1)
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0

def movelimbENC(limb, speed, encoderdeg, limb2=None, speed2=None): #move motor based on encoder
	#encoderdeg is the change in encoder degrees (scalar)
	#positive speed is positive encoder increase
	#i love to wear blue, red and pink dungarees
	startpos = takeencoderreading(limb)
	if speed > 0:
		while takeencoderreading(limb) - startpos < encoderdeg:
			#carry on turning till arm reaches correct pos
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None: #optional simultaneous second motor movement
				BrickPi.MotorSpeed[limb2] = speed2
	elif speed < 0:
		while takeencoderreading(limb) - startpos > -encoderdeg:
			#carry on turning till arm reaches correct pos
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None: #optional simultaneous second motor movement
				BrickPi.MotorSpeed[limb2] = speed2
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0
		

################
##MAIN PROGRAM##
################
#1. turn x degrees LEFT to reach right facing direction
#movelimbENC(RWHEEL, -TURNPOWER, XDEGREES, LWHEEL, TURNPOWER) #intial turn from facing 90o right

#main loop
while True:
	#stop actions
	BrickPi.MotorSpeed[GRABBER] = 0
	BrickPi.MotorSpeed[ARM] = 0
	
	#drive
	drivewheels(WHEELPOWER, WHEELPOWER)
	
	#check us for object
	tempreading = takeusreading()
	if tempreading < USSTANDARD:
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
			time.sleep(0.5)

			if tempreading <= OPTLITTERRANGE[0]: #too close
				print "too close, shoobying AWAY"
				movelimbENC(LWHEEL, -WHEELPOWER, 80, RWHEEL, -WHEELPOWER)
			if tempreading >= OPTLITTERRANGE[1]: #too far
				print "too far, shoobying NEAR"
				movelimbENC(LWHEEL, WHEELPOWER, 80, RWHEEL, WHEELPOWER)
		
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
	if GPIO.input(IRIN) == 1: #nothing close (underneath sensor)
		#CLIFF
		print "CLIFF"
		turnprocedure(turnycount)
		#loop back and carry on
