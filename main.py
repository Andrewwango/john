from BrickPi import *
import time
BrickPiSetup()

#if motors stalling - check voltage
#brickpiupdatevalues error - do system thingy
#if result=-1 - reboot


#define motors
#pos speed = rolling away from bum
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1
USSTANDARD = 20 #us sensor reading of floor
WHEELPOWER     = -200
GRABBERPOWER   =  100
LIFTPOWER      = -170
SLIDEDOWNPOWER =  100
OPENPOWER      = -40
BRINGDOWNPOWER =  150


BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1
BrickPi.MotorEnable[LWHEEL] = 1
BrickPi.MotorEnable[RWHEEL] = 1
BrickPiSetupSensors()
BrickPi.SensorType[HEAD] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()

def movelimb(limb, speed, length, grabberaswell=0):
		BrickPi.MotorSpeed[limb] = speed
		if grabberaswell=1:
			BrickPi.MotorSpeed[GRABBER] = GRABBERPOWER
		ot = time.time()
		while(time.time() - ot < length):
			BrickPiUpdateValues()
		time.sleep(.1)

#default pos is opened grabber, half down	

while True:
	#move wheels
	BrickPi.MotorSpeed[LWHEEL] = WHEELPOWER
	BrickPi.MotorSpeed[RWHEEL] = WHEELPOWER
	
	#get us reading
	uslist=[]
	for i in range(7):
		result = BrickPiUpdateValues()
		print result
		if not result :
			uslist += [int(BrickPi.Sensor[HEAD])]
		time.sleep(.05)
	print uslist
	usreading = max(set(uslist), key=uslist.count) #mode
	print "usreading is " + str(usreading)
	
	
	#check object detection
	if usreading < USSTANDARD:
		#object detected
		print "object detected"
		print "stopping"
		BrickPi.MotorSpeed[LWHEEL] = 0
		BrickPi.MotorSpeed[RWHEEL] = 0
		#shooby forward a wee
#		movelimb(LWHEEL, WHEELPOWER, 0.7)
#		movelimb(RWHEEL, WHEELPOWER, 0.7)
#		BrickPi.MotorSpeed[LWHEEL] = 0
#		BrickPi.MotorSpeed[RWHEEL] = 0
		
		time.sleep(1)
		print "sliding down"
		movelimb(ARM, SLIDEDOWNPOWER, 0.3)
		
		print "closing"
		movelimb(GRABBER, GRABBERPOWER, 0.5)
		time.sleep(0.5)
		
		print "lifting"
		movelimb(ARM, LIFTPOWER, 0.7, 1) #grabber grips as well

		print "opening"
		movelimb(GRABBER, OPENPOWER, 0.3)

		print "bringing down"
		movelimb(ARM, BRINGDOWNPOWER, 0.5)
		time.sleep(0.5)

		print "sliding down"
		movelimb(ARM, SLIDEDOWNPOWER, 0.3)
		
		time.sleep(2)
		break
