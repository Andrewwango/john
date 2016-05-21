from BrickPi import *

BrickPiSetup()
BrickPi.MotorEnable[PORT_A] = 1
BrickPi.MotorEnable[PORT_D] = 1

BrickPiSetupSensors()


BrickPi.MotorSpeed[PORT_D] = -200
BrickPi.MotorSpeed[PORT_A] = 200
ot = time.time()
while(time.time() - ot < 5):    #running while loop for 3 seconds
	BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
	time.sleep(.1)

