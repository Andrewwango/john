from BrickPi import *

BrickPiSetup()

BrickPi.MotorEnable[PORT_C] = 1

BrickPiSetupSensors()


while True:
    BrickPi.MotorSpeed[PORT_C] = -100

    ot = time.time()
    while(time.time() - ot < 1):    #running while loop for 3 seconds
        BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
	time.sleep(.1)
