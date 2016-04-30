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
print "starting to close"
BrickPi.MotorSpeed[grabber] = 80
BrickPiUpdateValues()
print "closing"
time.sleep(0.3)
print "finished waiting, stopping"
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
print "waiting"
time.sleep(5)

#this is open
print "starting to open"
BrickPi.MotorSpeed[grabber] = -80
BrickPiUpdateValues()
print "opening"
time.sleep(0.3)
print "finished waiting, stopping"
BrickPi.MotorSpeed[grabber] = 0
BrickPiUpdateValues()
print "waiting"
time.sleep(5)
