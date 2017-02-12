#TOP LEVEL CONSTANTS FOR MAIN.PY

import RPi.GPIO as GPIO
from BrickPi import *
GPIO.setmode(GPIO.BCM)

#Port Assignments
LWHEEL = PORT_D
RWHEEL = PORT_A
GRABBER = PORT_B
ARM = PORT_C
TOUCHR = PORT_1
TOUCHL = PORT_3

#GPIO Pins
IRIN = 25 #yellow (when sth close, 0)
US2TRIG = 24 #brown, out
US2ECHO = 23 #green, in
USNEWTRIG = 17 #out
USNEWECHO = 22 #in

XDEGREES=70.0 #angle between robot path and path (in degs) FLOAT POINT
USSTANDARD     = 30 #us sensor detection threshold
US2STANDARD    = 70 #higher us(2) detection threshold
OPTLITTERRANGE = [19,27] #the opt distance range from which it can pick up stuff
STOPRANGE=15.0

#Motor Power Constants
WHEELPOWER     = -255
TURNPOWER      = 100 #pos = forwards (for ease of use but not technically correct)
BRAKEPOWER     = -5  #"
SHOOBYPOWER    = -100
GRABBERPOWER   = -150
OPENPOWER      = 70
LIFTPOWER      = -160
SLIDEUPPOWER   = -70
BRINGDOWNPOWER = 120
BRINGDOWNBRAKEPOWER = -5

##SETUP## motors, sensors, GPIO Pins
BrickPi.MotorEnable[GRABBER] = 1 ; BrickPi.MotorEnable[ARM]    = 1
BrickPi.MotorEnable[LWHEEL]  = 1 ; BrickPi.MotorEnable[RWHEEL] = 1

BrickPi.SensorType[HEAD]   = TYPE_SENSOR_ULTRASONIC_CONT
BrickPi.SensorType[TOUCHL] = TYPE_SENSOR_TOUCH
BrickPi.SensorType[TOUCHR] = TYPE_SENSOR_TOUCH
BrickPiSetupSensors()

GPIO.setup(IRIN, GPIO.IN)
GPIO.setup(US2ECHO,   GPIO.IN) ; GPIO.setup(US2TRIG,   GPIO.OUT)
GPIO.setup(USNEWECHO, GPIO.IN) ; GPIO.setup(USNEWTRIG, GPIO.OUT)
