from BrickPi import *

BrickPiSetup()
BrickPiSetupSensors()
BrickPi.SensorType[PORT_4] = TYPE_SENSOR_ULTRASONIC_CONT
BrickPiSetupSensors()   #Send the properties of sensors to BrickPi

while True:
    result = BrickPiUpdateValues()  # Ask BrickPi to update values for sensors/motors 
    if not result :
        print BrickPi.Sensor[PORT_4]     #BrickPi.Sensor[PORT] stores the value obtained from sensor
    time.sleep(.05)     # sleep for 10 ms
