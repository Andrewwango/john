from BrickPi import *
import time

BrickPiSetup()
BrickPi.MotorEnable[PORT_C] = 1
BrickPiSetupSensors()

#down
BrickPi.MotorSpeed[PORT_C] = 60
ot = time.time()
while(time.time() - ot < 0.7):
	BrickPiUpdateValues()
	time.sleep(.1)

for i in range(5):

	#up
	BrickPi.MotorSpeed[PORT_C] = -60
	ot = time.time()
	while(time.time() - ot < 0.5):
		BrickPiUpdateValues()
		time.sleep(.1)		
		
	#down
	BrickPi.MotorSpeed[PORT_C] = 60
	ot = time.time()
	while(time.time() - ot < 0.5):
		BrickPiUpdateValues()
		time.sleep(.1)

#up
BrickPi.MotorSpeed[PORT_C] = -60
ot = time.time()
while(time.time() - ot < 0.7):
	BrickPiUpdateValues()
	time.sleep(.1)			
