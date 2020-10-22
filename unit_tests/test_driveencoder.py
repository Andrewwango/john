'''
Hardware test of angle encoder unit.
On running, robot should turn on the spot (right) and R motor encoder reading will be 
printed (increasing).
'''

from BrickPi import *
import time
import RPi.GPIO as GPIO

BrickPiSetup()
GPIO.setmode(GPIO.BCM)
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
HEAD = PORT_1
XDEGREES=260
WHEELPOWER     = -255
TURNPOWER      = 255 
SHOOBYPOWER    = -100
GRABBERPOWER   = -100
OPENPOWER      = 80
LIFTPOWER      = -200
BRINGDOWNPOWER = 100
BRINGDOWNBRAKEPOWER = -5
BrickPi.MotorEnable[GRABBER] = 1
BrickPi.MotorEnable[ARM] = 1
BrickPi.MotorEnable[LWHEEL] = 1
BrickPi.MotorEnable[RWHEEL] = 1
BrickPi.SensorType[HEAD] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()
turnycount = 1 #first turn is left (excluding initial)

def takeencoderreading(port): #read motor position
	result = BrickPiUpdateValues()
	if not result :
		print "encoder reading is: " + str(BrickPi.Encoder[port])
		return (BrickPi.Encoder[port])

#turn right
initial=takeencoderreading(RWHEEL)

while True:
	reading=takeencoderreading(RWHEEL)-initial
	BrickPi.MotorSpeed[RWHEEL] = 255; BrickPi.MotorSpeed[LWHEEL] = -255
	print reading
	if reading >=435:
		BrickPi.MotorSpeed[RWHEEL] = -5; BrickPi.MotorSpeed[LWHEEL] = 5
		break

