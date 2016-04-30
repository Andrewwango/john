from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()

grabber = PORT_D
BrickPi.MotorEnable[grabber] = 1
arm = PORT_A
BrickPi.MotorEnable[arm] = 1
#pos speed = rolling away from bum


print "closing"
BrickPi.MotorSpeed[grabber] = 40
ot = time.time()
while(time.time() - ot < 0.3):
	BrickPiUpdateValues()
time.sleep(.1)

print "opening"
BrickPi.MotorSpeed[grabber] = -40
ot = time.time()
while(time.time() - ot < 0.3):
	BrickPiUpdateValues()
time.sleep(.1)

print "lifting"
BrickPi.MotorSpeed[arm] = -150
ot = time.time()
while(time.time() - ot < 1):
	BrickPiUpdateValues()
time.sleep(.1)
