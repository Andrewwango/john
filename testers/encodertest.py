from BrickPi import *
BrickPiSetup()

BrickPi.MotorEnable[PORT_D] = 1
BrickPiSetupSensors()

result = BrickPiUpdateValues()
if not result :
    initialr = BrickPi.Encoder[PORT_A]

while True:
    result = BrickPiUpdateValues()
    if not result :
        print BrickPi.Encoder[PORT_A]-initialr
    time.sleep(.4)
