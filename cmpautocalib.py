import time
from BrickPi import *

SPEED=110 #pos acw first, cw 2nd

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

for i in range(2):
	if i==0: BrickPi.MotorSpeed[PORT_A]=-SPEED; BrickPi.MotorSpeed[PORT_D]= SPEED 
	else:    BrickPi.MotorSpeed[PORT_A]= SPEED; BrickPi.MotorSpeed[PORT_D]=-SPEED #turn back

	while True:
		result = BrickPiUpdateValues()
		if not result :
			encr = BrickPi.Encoder[PORT_A]-initialr
			print encr
			if abs(encr) > 1770: #a full turn
				break #finshed turning
		time.sleep(.1)

	BrickPi.MotorSpeed[PORT_A]=0; BrickPi.MotorSpeed[PORT_D]=0
	
#process results
