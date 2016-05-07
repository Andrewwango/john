from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()
BrickPi.SensorType[PORT_4] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()

#if motors stalling - check voltage
#brickpiupdatevalues error - do system thingy
#if result=-1 - reboot


#define motors
#pos speed = rolling away from bum
GRABBER = PORT_B
ARM = PORT_A
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1

#constants
USSTANDARD = 25 #us sensor reading of floor

def movelimb(limb, speed, length):
		BrickPi.MotorSpeed[limb] = speed
		ot = time.time()
		while(time.time() - ot < length):
			BrickPiUpdateValues()
		time.sleep(.1)

#default pos is opened grabber, half down	

while True:
	#get us reading
	uslist=[]
	for i in range(7):
		result = BrickPiUpdateValues()
		print result
		if not result :
			uslist += [int(BrickPi.Sensor[PORT_4])]
		time.sleep(.05)
	print uslist
	usreading = max(set(uslist), key=uslist.count) #mode
	print "usreading is " + str(usreading)

	if usreading < USSTANDARD and (USSTANDARD-usreading) > 5:
		#object detected
		print "object detected"

		print "sliding down"
		movelimb(ARM, 30, 0.3)
		
		print "closing"
		movelimb(GRABBER, 40, 0.3)
		
		print "lifting"
		movelimb(ARM, -150 0.7)

		print "opening"
		movelimb(GRABBER, -40, 0.3)

		print "bringing down"
		movelimb(ARM, 100, 0.5)
		
		print "sliding up"
		movelimb(ARM, -30, 0.3)
		
		time.sleep(2)
		break
