from BrickPi import *
import time
BrickPiSetup()
BrickPiSetupSensors()

grabber = PORT_D
BrickPi.MotorEnable[grabber] = 1
arm = PORT_A
BrickPi.MotorEnable[arm] = 1





print "closing"
BrickPi.MotorSpeed[PORT_D] = 30  #Set the speed of MotorB (-255 to 255)

ot = time.time()
while(time.time() - ot < 1):    #running while loop for 3 seconds
  BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
time.sleep(.1)

print "opening"
BrickPi.MotorSpeed[PORT_D] = -30  #Set the speed of MotorB (-255 to 255)

ot = time.time()
while(time.time() - ot < 1):    #running while loop for 3 seconds
    BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
time.sleep(.1)

    
