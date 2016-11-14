#//John (fully automated roadside litter picker)//#
#            //Started 29.05.16//v7//             #
#                //Andrew Wang//                  #
#BrickPi: github.com/DexterInd/BrickPi_Python
#import relevant modules
from BrickPi import *
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
BrickPiSetup()

'''ALGORITHM
- Start facing fowards, and turn x degrees to activate sweeping position
- Drive until US1 detects object.
	- Activate the higher US (US2)'s position
		- If object not detected, then object is small (litter). Perform picking procedure.
		- If object is  detected, then object is big(wall/edge). Perform turning procedure.
- If IR detects nothing, then it is far from ground(cliff/edge). Perform turning procedure.
'''

#DO

##CONSTANTS##
#Port Assignments
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_2
TOUCHR = PORT_1
TOUCHL = PORT_3

#GPIO Pins
IRIN = 25 #yellow (when sth close, 0)
US2TRIG = 24 #brown, out
US2ECHO = 23 #green, in

XDEGREES=380 #angle between robot path and path (in wheel encoderdegs)
             #min 363 (see John movement model)
USSTANDARD     = 20 #us sensor detection threshold
US2STANDARD    = 60 #higher us(2) detection threshold
OPTLITTERRANGE = [10,25] #the opt distance range from which it can pick up stuff

#Motor Power Constants
WHEELPOWER     = -255
TURNPOWER      = 180 #pos = forwards (for ease of use but not technically correct)
BRAKEPOWER     = -5  #"
SHOOBYPOWER    = -100
GRABBERPOWER   = -100
OPENPOWER      = 120
LIFTPOWER      = -200
SLIDEUPPOWER   = -70
BRINGDOWNPOWER = 120
BRINGDOWNBRAKEPOWER = -5

##SETUP## motors, sensors, GPIO Pins
BrickPi.MotorEnable[GRABBER] = 1 ; BrickPi.MotorEnable[ARM]    = 1
BrickPi.MotorEnable[LWHEEL]  = 1 ; BrickPi.MotorEnable[RWHEEL] = 1

BrickPi.SensorType[HEAD]   = TYPE_SENSOR_ULTRASONIC_CONT
BrickPi.SensorType[TOUCHL] = TYPE_SENSOR_TOUCH
BrickPi.SensorType[TOUCHR] = TYPE_SENSOR_TOUCH
BrickPiSetupSensors()

GPIO.setup(IRIN, GPIO.IN)
GPIO.setup(US2ECHO,   GPIO.IN)   ; GPIO.setup(US2TRIG,   GPIO.OUT)

turnycount = 1 #first turn is left(1) or right (0) (INCLUDING initial)
totElapsedTurningEnc = 0
tempElapsedTurningEnc = 0


#############
##FUNCTIONS##
#############

def takeus1reading(): #detect distance of bottom us
	#take 3 readings then find average
	uslist=[]
	for i in range(3):
		result = BrickPiUpdateValues()
		if not result:
			uslist += [int(BrickPi.Sensor[HEAD])]
		time.sleep(0.02)
	uslist.sort(); usreading = uslist[1] #median (get rid of anomalies)
	print "us1reading is " + str(usreading)
	return usreading

def takeus2reading(trig, echo): #detect distance of us2 (higher)
	GPIO.output(US2TRIG, False) #switch everything off
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
	print "US2 reading is " + str(usreading)
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
	global totElapsedTurningEnc
	#encoderdeg is the change in encoder degrees (scalar)
	#positive speed is positive encoder increase
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
				totElapsedTurningEnc = modifiedreading
				detectprocedure(True)
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0
		
def detectprocedure(alreadyturning):
	global tempElapsedTurningEnc
	#check US or touch for object
	tempreading = takeus1reading()
	temptouchreading = taketouchreadings()
	if tempreading < USSTANDARD or temptouchreading==1:
		print "object detected"
		drivewheels(0,0)
		
		#activate us2 pos
		if alreadyturning == False: #im not turning (so i want to activate us2 pos)
			print "sliding down bit by bit"
			movelimbENC(ARM, BRINGDOWNPOWER, 85)
			movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
			time.sleep(0.3)
		
		if alreadyturning==True:
			tempElapsedTurningEnc = totElapsedTurningEnc - tempElapsedTurningEnc

		#check higher us2 for big thing	
		if takeus2reading(US2TRIG, US2ECHO) > US2STANDARD:
			#LITTER (low-lying object)
			#pick up litter procedure
			print "low-lying object detected"
			time.sleep(0.5)
			
			#if while turning, turn back a wee to correct offshoot (only when turning quite a lot ie turning quickly)
			if alreadyturning == True and tempElapsedTurningEnc >= 100:
				#check which direction the normal turning is
				if turnycount%2 == 1: #odd=RIGHT (opposite to before)
					wheel1 = LWHEEL; wheel2 = RWHEEL
				else:
					wheel1 = RWHEEL; wheel2 = LWHEEL
				#use outside wheel to encode (although it doesn't matter)
				movelimbENC(wheel1, -TURNPOWER, 20, wheel2, TURNPOWER)
				movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake			
				time.sleep(0.2)
			
			#shooby
			if tempreading <= OPTLITTERRANGE[0]: #too close
				print "too close, shoobying AWAY"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
			elif tempreading >= OPTLITTERRANGE[1]: #too far
				print "too far, shoobying NEAR"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
			
			#grabber procedure
			print "bringing down" #get grabber into pos
			movelimbLENG(ARM, BRINGDOWNPOWER, 0.7)
			
			#preliminary grab
			movelimbLENG(GRABBER, GRABBERPOWER, 0.5, ARM, BRINGDOWNPOWER)
			
			print "lifting" #bring litter up
			movelimbLENG(ARM, LIFTPOWER, 0.7, GRABBER, GRABBERPOWER) #grabber grips as well

			print "opening" #dump litter
			movelimbLENG(GRABBER, OPENPOWER, 0.5)
			time.sleep(0.5)
			
			#move back if shoobied before
			if tempreading <= OPTLITTERRANGE[0]: #too close
				print "shoobying NEAR back to original pos"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
			elif tempreading >= OPTLITTERRANGE[1]: #too far
				print "shoobying AWAY back to original pos"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
			
		else:
			print "WALL" #WALL
			if alreadyturning == False: #im not turning already so i want to turn and deactivate at wall
				turnprocedure(XDEGREES*2)
			
				#bring us2 back up (deactivate)
				print "lifting"
				movelimbLENG(ARM, SLIDEUPPOWER, 0.3)
				#loop back and carry on
			elif alreadyturning == True: #im already turning so i want to get away from this goddamm wall
				print "turning away from goddamm wall"
				while takeus2reading(US2TRIG, US2ECHO) <= US2STANDARD:
					if turnycount%2 == 1: #odd=LEFT
						wheel1 = RWHEEL; wheel2 = LWHEEL
					else:
						wheel1 = LWHEEL; wheel2 = RWHEEL

					#turn until wall is no longer in sight (to get rid of stalling problem)
					BrickPi.MotorSpeed[wheel1] = -TURNPOWER; BrickPi.MotorSpeed[wheel2] = TURNPOWER
					BrickPiUpdateValues()
				BrickPi.MotorSpeed[wheel1] = 0; BrickPi.MotorSpeed[wheel2] = 0
				movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
				time.sleep(0.2)
								

################
##MAIN PROGRAM##
################
#initial turn from forwards
turnprocedure(XDEGREES)

#main loop
while True:
	try:
		#stop actions
		BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0

		drivewheels(WHEELPOWER, WHEELPOWER) #drive
		
		detectprocedure(False) #search for object
		
		#check IR for cliff
		if GPIO.input(IRIN) == 1: #nothing close (underneath sensor)
			#CLIFF - reverse
			print "CLIFF"
			movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
			turnprocedure(XDEGREES*2)
			#loop back and carry on]
	
	except KeyboardInterrupt:
		GPIO.cleanup()
