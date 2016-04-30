from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()

grabber = PORT_D
BrickPi.MotorEnable[grabber] = 1
arm = PORT_A
BrickPi.MotorEnable[arm] = 1


power = 200 #speed from -255 to 255

#this is close
BrickPi.MotorSpeed[grabber] = 80
BrickPiUpdateValues()
time.sleep(0.3)
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
time.sleep(2)

#this is open
BrickPi.MotorSpeed[grabber] = -80
BrickPiUpdateValues()
time.sleep(0.3)
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
time.sleep(2)
