from BrickPi import *
BrickPiSetup()
port=PORT_D
BrickPi.MotorEnable[port] = 1
BrickPiSetupSensors()

result = BrickPiUpdateValues()
if not result :
    initialr = BrickPi.Encoder[port]

while True:
    result = BrickPiUpdateValues()
    if not result :
        print BrickPi.Encoder[port]-initialr
    time.sleep(.4)
