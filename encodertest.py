from BrickPi import *
BrickPiSetup()

BrickPi.MotorEnable[PORT_C] = 1
BrickPiSetupSensors()

while True:
    result = BrickPiUpdateValues()
    if not result :
        print ( BrickPi.Encoder[PORT_C] ) /2
    time.sleep(.4)

# Note: One encoder value counts for 0.5 degrees. So 360 degrees = 720 enc. Hence, to get degress = (enc%720)/2
