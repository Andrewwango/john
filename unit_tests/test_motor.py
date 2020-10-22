'''
Hardware test of motors.
On running, motor at given port should run in one direction, then the other, then the original.
For 2 seconds each.
'''

import time
from BrickPi import *

port=PORT_D

BrickPiSetup()
BrickPi.MotorEnable[port]=1
BrickPiSetupSensors()


BrickPi.MotorSpeed[port]=-200
ot = time.time()
while(time.time() - ot < 2):    #running while loop for 3 seconds
	BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
	time.sleep(.1)
	

BrickPi.MotorSpeed[port]=200
ot = time.time()
while(time.time() - ot < 2):    #running while loop for 3 seconds
	BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
	time.sleep(.1)
	

BrickPi.MotorSpeed[port]=-200
ot = time.time()
while(time.time() - ot < 2):    #running while loop for 3 seconds
	BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
	time.sleep(.1)

