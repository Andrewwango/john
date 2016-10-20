'''DO
- get more casters printed
'''
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
- start facing fowards
- turn x degrees right
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
TOUCHR = PORT_2
TOUCHL = PORT_3

#GPIO Pins
IRIN = 25 #yellow (when sth close, 0)
USTRIG = 24 #brown, out
USECHO = 23 #green, in

XDEGREES=400 #angle between robot path and path (in wheel encoderdegs)
             #min 363 (see John movement model)
USSTANDARD     = 25 #us sensor detection threshold
US2STANDARD    = 70 #higher us(2) detection threshold
OPTLITTERRANGE = [10,15] #the opt distance range from which it can pick up stuff

#Motor Power Constants
WHEELPOWER     = -255
TURNPOWER      = 200 #pos = forwards (for ease of use but not technically correct)
BRAKEPOWER     = -5  #"
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
BrickPi.SensorType[TOUCHL] = TYPE_SENSOR_TOUCH
BrickPi.SensorType[TOUCHR] = TYPE_SENSOR_TOUCH
BrickPiSetupSensors()
turnycount = 1 #first turn is left(1) or right (0) (INCLUDING initial)


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
		time.sleep(0.02)
	uslist.sort(); usreading = uslist[4] #median (get rid of anomalies)
	print "usreading is " + str(usreading)
	return usreading
	
def takeus2reading(): #detect distance of us2 (higher)
	#take 5 readings then find average
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
	us2list.sort(); us2reading = us2list[2] #median (get rid of anomalies)
	print "higher us2reading is " + str(us2reading)
	return us2reading

def taketouchreadings():
	#check if any touch sensor is pressed
	result = BrickPiUpdateValues()
	if not result:
		if BrickPi.Sensor[TOUCHL]==1 or BrickPi.Sensor[TOUCHR]==1:
			print "TOUCH"
			return 1
		else:
			return 0

def takeencoderreading(port): #read motor position
	result = BrickPiUpdateValues()
	if not result :
		return (BrickPi.Encoder[port])

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower
	BrickPiUpdateValues()

def turnprocedure(deg): #turning procedure
	global turnycount
	time.sleep(0.5)
	#check if turn left or right
	if turnycount%2 == 1: #odd=left
		wheel1 = RWHEEL; wheel2 = LWHEEL
	else:
		wheel1 = LWHEEL; wheel2 = RWHEEL
		
	print "turnycount is" + str(turnycount)
	print "turning" #use outside wheel to encode (although it doesn't matter)
	movelimbENC(wheel1, -TURNPOWER, deg, wheel2, TURNPOWER, True)
	movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
	
	turnycount += 1 #next time turns other way
	time.sleep(0.5)	

def movelimbLENG(limb, speed, length, limb2=None, speed2=None): #move motor based on time length
	#set speeds
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None: #optional simultaneous second motor movement
		BrickPi.MotorSpeed[limb2] = speed2
	ot = time.time()
	while(time.time() - ot < length):
		BrickPiUpdateValues()
	time.sleep(0.1)
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0

def movelimbENC(limb, speed, encoderdeg, limb2=None, speed2=None, detection=False): #move motor based on encoder
	#encoderdeg is the change in encoder degrees (scalar)
	#positive speed is positive encoder increase
	global alreadyturning
	startpos = takeencoderreading(limb)
	if speed > 0:
		modifier=1
	elif speed < 0:
		modifier=-1
	while True:
		#carry on turning till arm reaches correct pos
		modifiedreading = (takeencoderreading(limb) - startpos)*modifier
		if modifiedreading >= encoderdeg:
			break #at final position
		
		BrickPi.MotorSpeed[limb] = speed
		if limb2 != None: #optional simultaneous second motor movement
			BrickPi.MotorSpeed[limb2] = speed2
		
		if detection==True: #litter detection while moving
			if modifiedreading >= 120: #turned enough so safe to start measuring for litter
				detectprocedure(True)
			
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0
		
def detectprocedure(alreadyturning):
	#check US or touch for object
	tempreading = takeusreading()
	temptouchreading = taketouchreadings()
	if tempreading < USSTANDARD or temptouchreading==1:
		print "object detected"
		drivewheels(0,0)
		
		#activate us2 pos
		if alreadyturning == False: #im not turning (so i want to activated pos)
			print "sliding down bit by bit"
			movelimbENC(ARM, BRINGDOWNPOWER, 80)
			movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
			time.sleep(0.3)

		#check higher us2 for big thing	
		if takeus2reading() > US2STANDARD:
			#LITTER (low-lying object)
			#pick up litter procedure
			print "low-lying object detected"
			time.sleep(0.5)

			if alreadyturning == False: #only correct position when not turning (or else it'll mess up the encoder)
				if tempreading <= OPTLITTERRANGE[0]: #too close
					print "too close, shoobying AWAY"
					movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
				if tempreading >= OPTLITTERRANGE[1]: #too far
					print "too far, shoobying NEAR"
					movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
		
			print "bringing down" #get grabber into pos
			movelimbLENG(ARM, BRINGDOWNPOWER, 0.7)
			
			#preliminary grab
			movelimbLENG(GRABBER, GRABBERPOWER, 0.5, ARM, BRINGDOWNPOWER)
			
			print "lifting" #bring litter up
			movelimbLENG(ARM, LIFTPOWER, 0.7, GRABBER, GRABBERPOWER) #grabber grips as well

			print "opening" #dump litter
			movelimbLENG(GRABBER, OPENPOWER, 0.5)
			time.sleep(0.5)
			
		else:
			print "WALL" #WALL
			if alreadyturning == False: #im not turning already so i want to turn and deactivate at wall
				turnprocedure(XDEGREES*2)
			
				#bring us2 back up (deactivate)
				print "lifting"
				movelimbLENG(ARM, LIFTPOWER, 0.1)
				#loop back and carry on

################
##MAIN PROGRAM##
################
#initial turn from forwards
turnprocedure(XDEGREES)

#main loop
while True:
	#stop actions
	BrickPi.MotorSpeed[GRABBER] = 0
	BrickPi.MotorSpeed[ARM] = 0
	#drive
	drivewheels(WHEELPOWER, WHEELPOWER)
	
	detectprocedure(False) #search for object
	
	#check IR for cliff
	if GPIO.input(IRIN) == 1: #nothing close (underneath sensor)
		#CLIFF - reverse
		print "CLIFF"
		movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
		turnprocedure(XDEGREES*2)
		#loop back and carry on
