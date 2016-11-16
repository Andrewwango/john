from BrickPi import *
import time

BrickPiSetup()
BrickPi.MotorEnable[PORT_C] = 1
BrickPiSetupSensors()

for i in range(5):
	#down
	BrickPi.MotorSpeed[PORT_C] = 120
	ot = time.time()
	while(time.time() - ot < 0.5):
		BrickPiUpdateValues()
		time.sleep(.1)
	#up
	BrickPi.MotorSpeed[PORT_C] = -150
	ot = time.time()
	while(time.time() - ot < 0.5):
		BrickPiUpdateValues()
		time.sleep(.1)		
		

