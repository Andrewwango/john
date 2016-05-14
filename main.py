from BrickPi import *
import time
BrickPiSetup()

##DEBUG##
#if motors stalling - check voltage + PSU
#brickpiupdatevalues error - do system thingy
#if result=-1 - reboot

##NOTES##
#default position is opened grabber, half down	
#positive speed = rolling away from bum

##CONSTANTS##
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1
USSTANDARD = 25 #us sensor threshold
WHEELPOWER     = -100
GRABBERPOWER   =  -100
LIFTPOWER      = -230
SLIDEDOWNPOWER =  60
OPENPOWER      = 40
BRINGDOWNPOWER =  100
SLIDEUPPOWER = -60
TURNPOWER = -255


##SETUP##
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1
BrickPi.MotorEnable[LWHEEL] = 1
BrickPi.MotorEnable[RWHEEL] = 1
BrickPi.SensorType[HEAD] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()


##FUNCTIONS##
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
	#take 7 readings then find mode
	uslist=[]
	BrickPi.MotorSpeed[GRABBER] = OPENPOWER #make sure grabber dunt interfere with reading
	for i in range(9):
		result = BrickPiUpdateValues()
		#print result
		if not result:
			uslist += [int(BrickPi.Sensor[HEAD])]
		time.sleep(.05)
	print uslist
	BrickPi.MotorSpeed[GRABBER] = 0
	#usreading = max(set(uslist), key=uslist.count) #mode
	#usreading = sum(uslist)/len(uslist) #mean
	print "usreading is " + str(usreading)
	return usreading

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower	

##MAIN LOOP##
while True:
	#stop actions
	BrickPi.MotorSpeed[GRABBER] = 0
	BrickPi.MotorSpeed[ARM] = 0
	#drive
	drivewheels(WHEELPOWER, WHEELPOWER)
		
	
	#check object detection
	if takeusreading() < USSTANDARD:
		print "object detected"
		
		#stop and slide up to check
		print "stopping and checking"
		drivewheels(0,0)
		movelimb(ARM, SLIDEUPPOWER, 0.2)
		time.sleep(0.2)
		
		if takeusreading() > USSTANDARD:
			#low-lying object
		
			print "low-lying object detected"
			
			time.sleep(1)
			print "sliding down"
			movelimb(ARM, SLIDEDOWNPOWER, 0.5)
			time.sleep(0.2)
			
			#shooby forward a wee
			print "shooby"
			movelimb(LWHEEL,  WHEELPOWER, 0.3, RWHEEL,  WHEELPOWER)
			drivewheels(0,0)			
			
			#preliminary grab
			movelimb(GRABBER, GRABBERPOWER, 0.4)
			
			print "lifting"
			movelimb(ARM, LIFTPOWER, 0.7, GRABBER, GRABBERPOWER) #grabber grips as well

			print "opening"
			movelimb(GRABBER, OPENPOWER, 0.5)

			print "bringing down"
			movelimb(ARM, BRINGDOWNPOWER, 0.3)
			time.sleep(0.5)
			
			time.sleep(2)
		else:
			#wall
			print "wall: sliding down"
			movelimb(ARM, SLIDEDOWNPOWER, 0.3)
			time.sleep(1)
			
			#reverse, turn right, go, then turn right again
			movelimb(LWHEEL, -WHEELPOWER, 0.4, RWHEEL, -WHEELPOWER)
			movelimb(LWHEEL,  TURNPOWER, 2, RWHEEL, -TURNPOWER)			
			movelimb(LWHEEL,  WHEELPOWER, 0.4, RWHEEL,  WHEELPOWER)
			movelimb(LWHEEL,  TURNPOWER, 2, RWHEEL, -TURNPOWER)
			drivewheels(0,0)	
