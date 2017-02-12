import time
from BrickPi import *

SPEED=110 #pos acw

BrickPiSetup()
BrickPi.MotorEnable[PORT_A]=1
BrickPi.MotorEnable[PORT_D]=1
BrickPiSetupSensors()
initialr=0;encr=0

while True: #make sure we get an encoder reading! (break when we do)
	result = BrickPiUpdateValues()
	if not result :
		initialr = BrickPi.Encoder[PORT_A]
		break

BrickPi.MotorSpeed[PORT_A]=-SPEED
BrickPi.MotorSpeed[PORT_D]=SPEED
while True:
	result = BrickPiUpdateValues()
	if not result :
		encr = BrickPi.Encoder[PORT_A]-initialr
		print encr
		if encr > 100:
			break #finshed turning
	time.sleep(.1)

#process results
