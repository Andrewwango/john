import time, math, smbus
from BrickPi import *

SPEED=110 #pos acw first, cw 2nd
scale = 0.92; minx = 0; maxx = 0; miny = 0; maxy = 0

BrickPiSetup()
BrickPi.MotorEnable[PORT_A]=1
BrickPi.MotorEnable[PORT_D]=1
BrickPiSetupSensors()

bus = smbus.SMBus(1)
address = 0x1e #i2c
f = open('mainsettings.dat', 'w')
f.write('hello!')

def read_word(adr):
	high = bus.read_byte_data(address, adr)
	low = bus.read_byte_data(address, adr+1)
	val = (high << 8) + low
	return val

def read_word_2c(adr):
	val = read_word(adr)
	if (val >= 0x8000): return -((65535 - val) + 1)
	else: return val

def write_byte(adr, value):
	bus.write_byte_data(address, adr, value)

write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000) # Continuous sampling

for i in range(2):
	initialr=0;encr=0
	
	while True: #make sure we get an encoder reading! (break when we do)
		result = BrickPiUpdateValues()
		if not result :
			initialr = BrickPi.Encoder[PORT_A]
			break

	if i==0: BrickPi.MotorSpeed[PORT_A]=-SPEED; BrickPi.MotorSpeed[PORT_D]= SPEED 
	else:    BrickPi.MotorSpeed[PORT_A]= SPEED; BrickPi.MotorSpeed[PORT_D]=-SPEED #turn back

	while True:
		result = BrickPiUpdateValues()
		if not result :
			encr = BrickPi.Encoder[PORT_A]-initialr
			print encr
			if abs(encr) > 40: #1770: #a full turn
				break #finshed turning
		#read compass
		x_out = read_word_2c(3)
		y_out = read_word_2c(7)
		z_out = read_word_2c(5)

		if x_out < minx: minx=x_out
		if y_out < miny: miny=y_out
		if x_out > maxx: maxx=x_out
		if y_out > maxy: maxy=y_out
			
		time.sleep(.1)

	BrickPi.MotorSpeed[PORT_A]=0; BrickPi.MotorSpeed[PORT_D]=0
	time.sleep(0.4)
	
#process results
x_offset = (maxx + minx) / 2
y_offset = (maxy + miny) / 2
print "x offset: ", x_offset
print "y offset: ", y_offset
data=str(x_offset) + "\n" + str(y_offset)
print data
for i in range(5):
	f.write(data)
f.close()
print "file written"
