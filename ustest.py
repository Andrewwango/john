from BrickPi import *

BrickPiSetup()
GRABBER = PORT_B
ARM = PORT_A
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1

print "opening"
BrickPi.MotorSpeed[GRABBER] = -40
ot = time.time()
while(time.time() - ot < 0.3):
	BrickPiUpdateValues()
time.sleep(.1)
