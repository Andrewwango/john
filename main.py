#//John (fully automated roadside litter picker)//#
#            //Started 29.05.16//v11//             #
#                //Andrew Wang//                  #
#BrickPi: github.com/DexterInd/BrickPi_Python
#remember to ./stopev.sh (disable getty via systemctl) on boot!
#import relevant modules
import time, math, lirc, sys, pygame, os, cmpautocalib
from BrickPi import *
from compassgpsutils import *
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
BrickPiSetup()
sockid = lirc.init("main",blocking=False)
clock=pygame.time.Clock()

#Port Assignments  ;    #GPIO Pins
LWHEEL = PORT_D    ;    IRIN     = 25 #yellow in (when sth close, 0)
RWHEEL = PORT_A    ;    US2TRIG  = 24 #brown, out
GRABBER= PORT_B    ;    US2ECHO  = 23 #green, in
ARM    = PORT_C    ;    USNEWTRIG= 17 #out
TOUCHR = 11        ;    USNEWECHO= 22 #in
TOUCHL = 4         ;    BUZZOUT  = 7  #out
''''''             ;    IRRCINT  = 8  #irrc interrupt pin
''''''             ;    SHUTBUTT = 9  #force shutdown button

XDEGREES = 60.0 #angle between robot path and path (in degs) FLOAT POINT
USSTANDARD     = 30 #us sensor detection threshold
US2STANDARD    = 70 #higher us(2) detection threshold
OPTLITTERRANGE = [19,27] #the opt us distance range from which it can pick up stuff
STOPRANGE = 15.0 #the allowable range for turnbear

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
BrickPi.SensorType[TOUCHL] = TYPE_SENSOR_TOUCH
BrickPi.SensorType[TOUCHR] = TYPE_SENSOR_TOUCH
BrickPiSetupSensors()

GPIO.setup(IRIN     , GPIO.IN)  ; GPIO.setup(BUZZOUT , GPIO.OUT)
GPIO.setup(USNEWECHO, GPIO.IN)  ; GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)
GPIO.setup(USNEWTRIG, GPIO.OUT) ; GPIO.setup(TOUCHL  , GPIO.IN , pull_up_down=GPIO.PUD_UP)
GPIO.setup(US2ECHO  , GPIO.IN)  ; GPIO.setup(TOUCHR  , GPIO.IN , pull_up_down=GPIO.PUD_UP)
GPIO.setup(US2TRIG  , GPIO.OUT) ; GPIO.setup(IRRCINT , GPIO.IN)

##PROGRAM VARS##
turnycount = 0 #first turn is left(1) or right (0) (INCLUDING initial)
totElapsedTurningEnc = 0
tempElapsedTurningEnc = 0
turnbears=[]
shoobied='no'
debouncetimestamp = time.time()

####PROCESS GPX FILE (EXTRACT CDP)
####
cdp=[[0,0,225]] #adjust for testing
currentcdp = 0

#EXTRACT FWDB (local for demo) - real thing: change every cdp
settingsfile = open('mainsettings.dat','r')
origfwdb=float(settingsfile.read().split('\n')[2])
settingsfile.close()
print 'origfwdb ', origfwdb

#############
##FUNCTIONS##
#############
		
def buzz(patternofbuzz):
	patternofbuzz = patternofbuzz.split()
	for i in range(len(patternofbuzz)):
		GPIO.output(BUZZOUT, True)
		if patternofbuzz[i]=="short" : time.sleep(0.1)
		elif patternofbuzz[i]=="long": time.sleep(0.3)
		GPIO.output(BUZZOUT, False)
		if len(patternofbuzz) >= 1 and i != len(patternofbuzz)-1: time.sleep(0.2) #if more than one beep and not at end
		
def takeusreading(trig, echo): #detect distance of a us
	GPIO.output(trig, False) #switch everything off
	#take 5 readings then find average
	uslist=[]
	for i in range(3):
		#send out signal
		GPIO.output(trig, False)
		time.sleep(0.001)
		GPIO.output(trig, True)
		time.sleep(0.001)
		GPIO.output(trig, False)
		
		#find length of signal
		start = time.time()
		stop = time.time()
		while GPIO.input(echo) == 0:
			start = time.time()
		while GPIO.input(echo) == 1:
			stop = time.time()
		duration = stop - start
		
		#find length
		distance = duration * 340 * 100 #cm
		uslist += [int(distance)]
		time.sleep(0.01)
	uslist.sort(); usreading = uslist[1] #median (get rid of anomalies)
	GPIO.output(trig, False)
	print "US reading is ", str(usreading), uslist
	return usreading

def taketouchreadings():
	#check if any touch sensor is pressed
	if GPIO.input(TOUCHL) or GPIO.input(TOUCHR) == 0: return 1
	else: return 0 #look for falling edge

def takeencoderreading(port): #read motor position
	for i in range(3): #deal with encoder glitches
		result = BrickPiUpdateValues()
		if not result :
			return (BrickPi.Encoder[port])
	return 0 #better than nonetype

def drivewheels(lpower, rpower):
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower
	BrickPiUpdateValues()

def createturnbears():
	#create list of bearings for each turn
	turnbears=[fwdb-XDEGREES,fwdb+XDEGREES] #l,r
	#correct to 0<b<360
	for i in range(len(turnbears)):
		if turnbears[i] > 360: turnbears[i] -= 360
		if turnbears[i] < 0  : turnbears[i] += 360
	print turnbears; return turnbears

def grabprocedure(): #picking procedure
	print "bringing down" #get grabber into pos
	movelimbLENG(ARM, BRINGDOWNPOWER, 0.6)

	#preliminary grab
	movelimbLENG(GRABBER, GRABBERPOWER, 0.5, ARM, BRINGDOWNPOWER)

	print "lifting" #bring litter up
	movelimbLENG(ARM, LIFTPOWER, 0.6, GRABBER, GRABBERPOWER) #grabber grips as well

	print "opening" #dump litter
	movelimbLENG(GRABBER, OPENPOWER, 0.5)
	time.sleep(0.5)	

def turnprocedure(): #turning procedure
	global turnycount; global turnbears
	time.sleep(0.5)
	
	#setup wheels depending on direction to turn
	if turnycount%2 == 1: #odd=left
		wheel1 = RWHEEL; wheel2 = LWHEEL
		targBear = turnbears[0]
	else: #right
		wheel1 = LWHEEL; wheel2 = RWHEEL
		targBear = turnbears[1]
	
	print "turning", turnycount
	movelimbENC(wheel1, -TURNPOWER, targBear, wheel2, TURNPOWER, detection=True, compass=True)
	movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
	
	turnycount += 1 #next time turns other way
	time.sleep(0.5)	

def movelimbLENG(limb, speed, length, limb2=None, speed2=None): #move motor based on time length
	#set speeds
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None: #optional simultaneous second motor movement
		BrickPi.MotorSpeed[limb2] = speed2
	#time movement
	ot = time.time()
	while(time.time() - ot < length):
		BrickPiUpdateValues()
	time.sleep(0.1)
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0

def movelimbENC(limb, speed, deg, limb2=None, speed2=None, detection=False, compass=False): #move motor based on encoder OR COMPASS
	global totElapsedTurningEnc
	#deg is the change in encoder degrees (scalar) OR compass deg if compass=True
	#positive speed is positive encoder increase
	startpos = takeencoderreading(limb)
	if speed > 0:
		modifier=1
	elif speed < 0:
		modifier=-1
	
	if compass==False: #in this instance turn based on encoder
		while True:
			#carry on turning till limb reaches correct pos
			modifiedreading = (takeencoderreading(limb) - startpos)*modifier
			if modifiedreading >= deg:
				break #at final position
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None: #optional simultaneous second motor movement
				BrickPi.MotorSpeed[limb2] = speed2
			
	elif compass==True: #in this instance turn based on COMPASS
		while True:
			modifiedreading = (takeencoderreading(limb) - startpos)*modifier #encoder shiz
			
			#carry on turning till reaches correct bearing
			if abs(takebearing()-deg) <= STOPRANGE: #range of stopping
				break
				
			BrickPi.MotorSpeed[limb] = speed
			
			if limb2 != None: #optional simultaneous second motor movement
				BrickPi.MotorSpeed[limb2] = speed2
			
			if detection==True: #litter detection while turning
				if modifiedreading >= 120: #turned enough so safe to start measuring for litter
					totElapsedTurningEnc = modifiedreading
					detectprocedure(True)
	
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0
		
def detectprocedure(alreadyturning):
	global tempElapsedTurningEnc
	#check US or touch for object
	tempreading = takeusreading(USNEWTRIG,USNEWECHO)
	temptouchreading = taketouchreadings()
	if tempreading < USSTANDARD or temptouchreading==1:
		print "object detected"
		buzz("long")
		drivewheels(0,0)
		
		#activate us2 pos
		if alreadyturning == False and temptouchreading==0: #im not turning (so i want to activate us2 pos)
			print "sliding down bit by bit, activate"
			movelimbENC(ARM, BRINGDOWNPOWER, 85)
			movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
			time.sleep(0.7)
		
		if alreadyturning==True:
			tempElapsedTurningEnc = totElapsedTurningEnc - tempElapsedTurningEnc

		#check higher us2 for big thing	
		if takeusreading(US2TRIG, US2ECHO) > US2STANDARD and temptouchreading==0:
			#LITTER (low-lying object)
			buzz("short short")
			#pick up litter procedure
			print "low-lying object detected"
			time.sleep(0.5)
			
			#if while turning, turn back a wee to correct offshoot (only when turning quite a lot ie turning quickly)
			if alreadyturning == True and tempElapsedTurningEnc >= 100:
				#check which direction the normal turning is
				if turnycount%2 == 1: #odd=RIGHT (opposite to before)
					wheel1 = LWHEEL; wheel2 = RWHEEL
				else:
					wheel1 = RWHEEL; wheel2 = LWHEEL
				#use outside wheel to encode (although it doesn't matter)
				movelimbENC(wheel1, -TURNPOWER, (int(2.3*math.sqrt(tempElapsedTurningEnc))),wheel2, TURNPOWER)#fine tune this
				movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake			
				time.sleep(0.2)
			
			#shooby
			shoobied='no'
			if tempreading <= OPTLITTERRANGE[0]: #too close
				print "too close, shoobying AWAY"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
				shoobied='away'
			elif tempreading >= OPTLITTERRANGE[1]: #too far
				print "too far, shoobying NEAR"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
				shoobied='near'
			
			grabprocedure()
			
			#move back if shoobied before
			if shoobied=='away':
				print "shoobying NEAR back to original pos"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
			elif shoobied=='near':
				print "shoobying AWAY back to original pos"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
			
		else:
			print "WALL" #WALL(either by us or touch)
			buzz("long")
			if alreadyturning == False: #im not turning already so i want to turn and deactivate at wall
				turnprocedure()
			
				#bring us2 back up (deactivate)
				print "sliding up, deactivate"
				movelimbLENG(ARM, SLIDEUPPOWER, 0.3)
				#loop back and carry on
			elif alreadyturning == True: #im already turning so i want to get away from this goddamm wall
				print "turning away from goddamm wall"
				while takeusreading(US2TRIG, US2ECHO) <= US2STANDARD:
					if turnycount%2 == 1: #odd=LEFT
						wheel1 = RWHEEL; wheel2 = LWHEEL
					else:
						wheel1 = LWHEEL; wheel2 = RWHEEL

					#turn until wall is no longer in sight (to get rid of stalling problem)(manual turn)
					BrickPi.MotorSpeed[wheel1] = -TURNPOWER; BrickPi.MotorSpeed[wheel2] = TURNPOWER
					BrickPiUpdateValues()
				movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
				BrickPi.MotorSpeed[wheel1] = 0; BrickPi.MotorSpeed[wheel2] = 0

				time.sleep(0.2)
								
def restartprogram(channel):
	global debouncetimestamp
	timenow = time.time()
	#handle button being pressed when main is running - restart (essentially, stop)
	if timenow - debouncetimestamp >= 0.3: #debounce ir so only 1 interrupt
		print "taking action on interrupt"
		if startmain == True: #only restart program if main is actually running!
			BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0; drivewheels(0,0) #stop all
			buzz("short long")
			GPIO.cleanup()
			print "Stop pressed - Restarting program"
			os.execl(sys.executable, sys.executable, *sys.argv)
	debouncetimestamp = timenow

def shutdownprogram(channel):
	global debouncetimestamp
	timenow = time.time()
	if timenow - debouncetimestamp >= 0.3: #debounce ir so only 1 interrupt
		buzz("short short short short")
		print "shutbutt pressed, shutting down"
		GPIO.cleanup()
	debouncetimestamp = timenow

#set GPIO interrupts
GPIO.add_event_detect(IRRCINT, GPIO.RISING, callback=restartprogram)
GPIO.add_event_detect(SHUTBUTT,GPIO.FALLING,callback=shutdownprogram) 
					
################
##MAIN PROGRAM##
################
startmain = False
while True:
	try:
		clock.tick(10)
		#IRRC handling loop
		ircode = lirc.nextcode()
		if ircode:
			fwdb=0
			if ircode[0] == "startmainfwdleft":
				turnycount = 1 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0]=="startmainfwdright":
				turnycount = 0 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0]=="startmainbwdleft":
				turnycount = 1 ; fwdb = origfwdb + 180.0 ; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0]=="startmainbwdright":
				turnycount = 0 ; fwdb = origfwdb + 180.0 ; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0]=="startshutdown":
				print "Shutting down!"
				buzz("short short short short")
			elif ircode[0]=="startcmpautocalib":
				print "starting calibration script"
				buzz("long long")
				cmpautocalib.maincalibprogram()
			elif ircode[0]=="bants":
				buzz("long long short short long short short short long short short")
			if fwdb > 360.0: fwdb -= 360.0
			print turnycount, fwdb
		

		
		if startmain == True:
			print "main has started"
			#initial stuff
			turnbears = createturnbears()
			
			#bring arm back up in case it's not
			movelimbLENG(ARM, SLIDEUPPOWER, 0.3)

			#initial turn from forwards
			turnprocedure()

			#main loop
			while True:
				try:
					#stop actions
					BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0

					#drive
					drivewheels(WHEELPOWER, WHEELPOWER)

					#search for object
					detectprocedure(False)

					#check IR for cliff
					if GPIO.input(IRIN) == 1: #nothing close (underneath sensor)
						print "CLIFF"
						#reverse!
						movelimbENC(LWHEEL, -WHEELPOWER, 130, RWHEEL, -WHEELPOWER)
						buzz("long")
						turnprocedure()
						#loop back and carry on

					#check if routepoint reached
					for i in range(3):
						pass
						#get gps coords
						#check if within +=0.00001
					#if reached cdp, cdp steering procedure (use compass to control)
					#make new turnbears based on current cdp
				except KeyboardInterrupt:
					GPIO.cleanup()
					sys.exit()
	except KeyboardInterrupt:
		GPIO.cleanup()
		sys.exit()
