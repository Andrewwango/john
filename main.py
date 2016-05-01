from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()
BrickPi.SensorType[PORT_4] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()

#define motors
#pos speed = rolling away from bum
GRABBER = PORT_B
ARM = PORT_A
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1

#constants
USSTANDARD = 25 #us sensor reading of floor

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
	try:
		usreading = max(set(uslist), key=uslist.count) #mode
	except:
		continue
	print "usreading is " + str(usreading)

	if usreading < USSTANDARD and (USSTANDARD-usreading) > 5:
		#object detected
		print "object detected"
		time.sleep(2)
	





