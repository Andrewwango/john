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

BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1
BrickPi.MotorEnable[LWHEEL] = 1
BrickPi.MotorEnable[RWHEEL] = 1
BrickPiSetupSensors()
BrickPi.SensorType[HEAD] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()

def movelimb(limb, speed, length):
		BrickPi.MotorSpeed[limb] = speed
		ot = time.time()
		while(time.time() - ot < length):
			BrickPiUpdateValues()
		time.sleep(.1)

#default pos is opened grabber, half down	

while True:
	#move wheels
	BrickPi.MotorSpeed[LWHEEL] = -120
	BrickPi.MotorSpeed[RWHEEL] = -120
	
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
		BrickPi.MotorSpeed[LWHEEL] = 0
		BrickPi.MotorSpeed[RWHEEL] = 0		
		
		time.sleep(1)
		print "sliding down"
		movelimb(ARM, 60, 0.3)
		
		print "closing"
		movelimb(GRABBER, 40, 0.3)
		
		print "lifting"
		movelimb(ARM, -150, 0.7)

		print "opening"
		movelimb(GRABBER, -40, 0.3)

		print "bringing down"
		movelimb(ARM, 150, 0.5)
		
		time.sleep(0.5)
		
#		print "sliding up"
#		movelimb(ARM, -20, 0.3)
		
		time.sleep(2)
		break
