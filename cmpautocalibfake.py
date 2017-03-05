import time, math, smbus
from BrickPi import *
import RPi.GPIO as GPIO

SPEED=180 #pos acw first, cw 2nd
BUZZOUT  = 7 #buzzer pin
IRRCINT  = 8  #irrc interrupt pin
scale = 0.92
breaking = False

BrickPiSetup()
BrickPi.MotorEnable[PORT_A]=1 ; BrickPi.MotorEnable[PORT_D]=1
BrickPiSetupSensors()

#setup i2c
bus = smbus.SMBus(1)
address = 0x1e #i2c address

def returnprogram(channel):
	global breaking; breaking = True


def buzz():
	for i in range(2):
		GPIO.output(BUZZOUT, True)  ; time.sleep(0.3)
		GPIO.output(BUZZOUT, False) ; time.sleep(0.2)

#compass I2C functions
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

def maincalibprogram():
	global breaking
	
	#interrupt pin set here so it doesn't interfere with main's IRRCINT
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM); GPIO.setup(BUZZOUT, GPIO.OUT) ; GPIO.setup(IRRCINT , GPIO.IN)
	GPIO.add_event_detect(IRRCINT, GPIO.RISING, callback=returnprogram) #in func so it doesn't disturb with main
	
	minx = 0; maxx = 0; miny = 0; maxy = 0
	
	for i in range(2):
		initialr=0;encr=0
		
		if breaking == True: break

		while True: #make sure we get an encoder reading! (break when we do)
			result = BrickPiUpdateValues()
			if not result :
				initialr = BrickPi.Encoder[PORT_A]
				break

		if i==0: BrickPi.MotorSpeed[PORT_A]=-SPEED; BrickPi.MotorSpeed[PORT_D]= SPEED 
		else:    BrickPi.MotorSpeed[PORT_A]= SPEED; BrickPi.MotorSpeed[PORT_D]=-SPEED #turn back
		
		while True:
			if breaking == True: break
			
			result = BrickPiUpdateValues()
			if not result :
				encr = BrickPi.Encoder[PORT_A]-initialr
				print encr
				if abs(encr) > 1767: #a full turn
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
	
	if breaking == True:
		print "cmpautocalib interrupted, returning to main"
		buzz();	GPIO.cleanup()
		return #leave program and return to main
	
	#process results
	x_offset = (maxx + minx) / 2
	y_offset = (maxy + miny) / 2
	print "x offset: ", x_offset
	print "y offset: ", y_offset

	#make local fwdb (for demo)
	print "FACE JOHN FORWARDS"
	buzz(); time.sleep(10)
	print "making fwdb!"
	x_out = (read_word_2c(3) - x_offset) * scale
	y_out = (read_word_2c(7) - y_offset) * scale
	z_out = (read_word_2c(5)) * scale
	fwdb = math.atan2(y_out, x_out) 
	if (fwdb < 0):
		fwdb += 2 * math.pi
	fwdb = int(math.degrees(fwdb))
	print "fwdb: ", fwdb

	f = open('mainsettings.dat', 'w')
	f.write(str(x_offset) + "\n" + str(y_offset) + "\n" + str(fwdb) + "\n" + "0")
	print "file written" #saved to pi directory
	f.close(); buzz(); GPIO.cleanup(); print "cmpautocalib completed"

maincalibprogram()
