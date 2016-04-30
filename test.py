from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()

grabber = PORT_D
BrickPi.MotorEnable[grabber] = 1
arm = PORT_A
BrickPi.MotorEnable[arm] = 1


power = 200 #speed from -255 to 255

#this is wards
BrickPi.MotorSpeed[grabber] = 40
BrickPiUpdateValues()
time.sleep(2)
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
time.sleep(2)

#this is wards
BrickPi.MotorSpeed[grabber] = -40
BrickPiUpdateValues()
time.sleep(2)
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
time.sleep(2)
