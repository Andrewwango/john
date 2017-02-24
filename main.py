#!/usr/bin/env python2.7
###################################################
#//JOHN (fully automated roadside litter picker)//#
#                    //main.py//                  #
#         //Started 29.05.16//v14//21.02.17       #
#                //ANDREW WANG//                  #
#            //All Rights Reserved//              #
# //BrickPi: github.com/DexterInd/BrickPi_Python//#
###################################################
#v14 makes new detection correction.

#Import relevant modules
import time, math, lirc, sys, pygame, os, cmpautocalib
from BrickPi import *
from compassgpsutils import *
import RPi.GPIO as GPIO

#Initial setup
GPIO.setmode(GPIO.BCM)                   #set GPIO numbering
BrickPiSetup()                           #setup BrickPi interface
sockid = lirc.init("main",blocking=False)#setup infrared RC
clock=pygame.time.Clock()                #setup FPS clock

#Port Assignments  ;    #GPIO Pins
LWHEEL = PORT_D    ;    IRIN     = 25 #yellow in (when sth close, 0)
RWHEEL = PORT_A    ;    US2TRIG  = 24 #brown, out- high US sensor
GRABBER= PORT_B    ;    US2ECHO  = 23 #green, in - high US sensor
ARM    = PORT_C    ;    USNEWTRIG= 17 #purple,out- low  US sensor
''''''             ;    USNEWECHO= 22 #yellow,in - low  US sensor
''''''             ;    BUZZOUT  = 7  #brown, out- buzzer
''''''             ;    IRRCINT  = 8  #white, in - irrc interrupt pin
''''''             ;    TOUCHL   = 11 #blue,  in - touch sensor
''''''             ;    TOUCHR   = 4  #green, in - touch sensor

#Constants
XDEGREES       = 80.0 #angle between robot path and path (in degs)(FLOAT)
USSTANDARD     = 37   #low us(new) sensor detection threshold
US2STANDARD    = 50   #high us(2) detection threshold
OPTLITTERRANGE = [19,28]#the opt us distance range from which it can pick up stuff
STOPRANGE      = 15.0 #the allowable range for turnbear

#Motor Power Constants
WHEELPOWER     = -170 #driving power
TURNPOWER      = 160  #pos = forwards (for ease of use but not technically correct)
BRAKEPOWER     = -5   #"
SHOOBYPOWER    = -100
GRABBERPOWER   = -170
OPENPOWER      = 70
LIFTPOWER      = -200
SLIDEUPPOWER   = -100  #deactivating arm
BRINGDOWNPOWER = 170
BRINGDOWNBRAKEPOWER = -5

##SETUP## motors, sensors, GPIO Pins
BrickPi.MotorEnable[GRABBER] = 1 ; BrickPi.MotorEnable[ARM]    = 1
BrickPi.MotorEnable[LWHEEL]  = 1 ; BrickPi.MotorEnable[RWHEEL] = 1
try: #catch error if getty wasn't disabled on boot
	BrickPiSetupSensors()
except OSError:
	os.system("sudo sh /home/pi/stopev.sh")
	os.execl(sys.executable, sys.executable, *sys.argv) #reboot
	

GPIO.setup(IRIN     , GPIO.IN)  ; GPIO.setup(BUZZOUT , GPIO.OUT)
GPIO.setup(USNEWECHO, GPIO.IN)
GPIO.setup(USNEWTRIG, GPIO.OUT) ; GPIO.setup(TOUCHL  , GPIO.IN , pull_up_down=GPIO.PUD_UP)
GPIO.setup(US2ECHO  , GPIO.IN)  ; GPIO.setup(TOUCHR  , GPIO.IN , pull_up_down=GPIO.PUD_UP)
GPIO.setup(US2TRIG  , GPIO.OUT) ; GPIO.setup(IRRCINT , GPIO.IN)

##PROGRAM VARS##
turnycount = 0 #first turn is left(1) or right (0) (INCLUDING initial)
turnbears = []
shoobied = 'no'
debouncetimestamp = time.time()

#Extract FWDB (forward bearing) from settings file
settingsfile = open('/home/pi/mainsettings.dat','r')
origfwdb = float(settingsfile.read().split('\n')[2])
settingsfile.close()
print 'origfwdb ', origfwdb

print "SETUP FINISHED"

#############
##FUNCTIONS##
#############
		
def buzz(patternofbuzz): #activate buzzer
	patternofbuzz = patternofbuzz.split()
	for i in range(len(patternofbuzz)):
		GPIO.output(BUZZOUT, True)
		if   patternofbuzz[i] == "short" : time.sleep(0.1)
		elif patternofbuzz[i] == "long"  : time.sleep(0.3)
		GPIO.output(BUZZOUT, False)
		if len(patternofbuzz) >= 1 and i != len(patternofbuzz)-1: time.sleep(0.2) #if more than one beep and not at end
		
def takeusreading(trig, echo): #take reading from ultrasonic sensor
	GPIO.output(trig, False) #switch everything off
	#take 4 readings then find average
	uslist=[]
	for i in range(4):
		#send out signal
		GPIO.output(trig, False); time.sleep(0.001)
		GPIO.output(trig, True);  time.sleep(0.001)
		GPIO.output(trig, False)
		
		#find length of signal
		start = time.time(); stop = time.time()
		while GPIO.input(echo) == 0: start = time.time()
		while GPIO.input(echo) == 1: stop  = time.time()
		duration = stop - start
		
		#find length
		distance = duration * 340 * 100 #cm from speed of sound
		uslist += [int(distance)]
		time.sleep(0.01)
	uslist.sort(); usreading = uslist[2] #median (get rid of anomalies)
	GPIO.output(trig, False)
	print "US reading is ", str(usreading), uslist
	return usreading

def taketouchreadings(): #check if any touch sensor is pressed
	stateL = GPIO.input(TOUCHL); stateR= GPIO.input(TOUCHR)
	if stateL == 0 or stateR == 0: return 1 #look for falling edge
	else: return 0

def takeencoderreading(port): #read motor position from built in encoder
	for i in range(3): #deal with encoder glitches
		result = BrickPiUpdateValues()
		if not result: return (BrickPi.Encoder[port])
	return 0 #better than nonetype

def drivewheels(lpower, rpower): #set wheels goin'
	BrickPi.MotorSpeed[LWHEEL] = lpower
	BrickPi.MotorSpeed[RWHEEL] = rpower
	BrickPiUpdateValues()

def createturnbears():
	#create list of bearings for each turn according to forward direction
	turnbears = [fwdb-XDEGREES , fwdb+XDEGREES] #l,r
	#correct to 0<b<360
	for i in range(len(turnbears)):
		if turnbears[i] > 360: turnbears[i] -= 360
		if turnbears[i] < 0  : turnbears[i] += 360
	print turnbears; return turnbears

def pickprocedure(): #LITTER PICKING PROCEDURE
	print "bringing down" #get grabber into correct position
	movelimbLENG(ARM, BRINGDOWNPOWER, 0.6)

	#preliminary grab
	movelimbLENG(GRABBER, GRABBERPOWER, 0.6, ARM, BRINGDOWNPOWER)

	print "lifting" #bring litter up
	movelimbLENG(ARM, LIFTPOWER, 0.6, GRABBER, GRABBERPOWER) #grabber grips as well

	print "opening" #dump litter
	movelimbLENG(GRABBER, OPENPOWER, 0.5); time.sleep(0.5)	

def turnprocedure(): #TURNING PROCEDURE
	global turnycount; global turnbears
	time.sleep(0.5)
	
	#setup wheels depending on direction to turn
	if turnycount%2 == 1: #odd=left
		wheel1 = RWHEEL; wheel2 = LWHEEL
		targBear = turnbears[0]
	else: #right
		wheel1 = LWHEEL; wheel2 = RWHEEL
		targBear = turnbears[1]
	
	#while turning, use compass for guidance, and search litter too
	print "turning", turnycount
	movelimbENC(wheel1, -TURNPOWER, targBear, wheel2, TURNPOWER, detection=True, compass=True)
	movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
	
	turnycount += 1 #next time turns other way
	time.sleep(0.5)	


def movelimbLENG(limb, speed, length, limb2=None, speed2=None): #move motor based on time length
	#set speed(s)
	BrickPi.MotorSpeed[limb] = speed
	if limb2 != None: BrickPi.MotorSpeed[limb2] = speed2 #optional simultaneous second motor movement
	
	#time movement
	ot = time.time()
	while(time.time() - ot < length): BrickPiUpdateValues()
	time.sleep(0.1)
	
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None: BrickPi.MotorSpeed[limb2] = 0


def movelimbENC(limb, speed, deg, limb2=None, speed2=None, detection=False, compass=False): #move motor based on encoder OR COMPASS guidance
	#this turns a motor until motor reaches certain encoder position OR John faces certain direction
	#deg is the change in: encoder degrees (scalar) OR compass deg if compass=True
	#for encoder, positive speed is positive encoder increase
	startpos = takeencoderreading(limb)
	#set directions
	if   speed > 0: modifier=1
	elif speed < 0: modifier=-1
	
	if compass == False: #in this instance turn based on encoder
		while True:
			#carry on turning till limb reaches correct pos
			modifiedreading = (takeencoderreading(limb) - startpos) * modifier
			if modifiedreading >= deg: break #at final position
			
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None: BrickPi.MotorSpeed[limb2] = speed2 #optional simultaneous second motor movement
			
	elif compass == True: #in this instance turn based on COMPASS
		while True:
			#carry on turning till reaches correct bearing
			modifiedreading = (takeencoderreading(limb) - startpos) * modifier #encoder shiz
			if abs(takebearing()-deg) <= STOPRANGE: break #at final bearing
				
			BrickPi.MotorSpeed[limb] = speed
			if limb2 != None: BrickPi.MotorSpeed[limb2] = speed2 #optional simultaneous second motor movement
			
			if detection==True: #litter detection while turning
				if modifiedreading >= 120: #turned enough so safe to start measuring for litter
					detectprocedure(True)
	
	#stop
	BrickPi.MotorSpeed[limb] = 0
	if limb2 != None:
		BrickPi.MotorSpeed[limb2] = 0

def turnwhilecondition(turnbackornot, trig, echo, op, val):
	if turnbackornot == "turnback": b = 1
	else: b = 0
	#set wheel directions
	if turnycount%2 == b: #direction is inputted by user
		wheel1 = LWHEEL; wheel2 = RWHEEL
	else:
		wheel1 = RWHEEL; wheel2 = LWHEEL

	while eval("takeusreading(trig, echo)" + op + "val"):
		#turn until condition is met
		BrickPi.MotorSpeed[wheel1] = -TURNPOWER; BrickPi.MotorSpeed[wheel2] = TURNPOWER
		BrickPiUpdateValues()

	try:
		movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
		drivewheels(0,0) #stop
	except UnboundLocalError: pass #errors are annoying
	time.sleep(0.4)
		
def detectprocedure(alreadyturning): #DETECTION PROCEDURE
	
	#check LOW US or touch for object
	tempreading      = takeusreading(USNEWTRIG,USNEWECHO)
	temptouchreading = taketouchreadings()
	if tempreading < USSTANDARD or temptouchreading == 1:
		#detected something!
		drivewheels(0,0) #stop
		print "object detected"; buzz("long")

		#activate HIGH US(2) pos
		if alreadyturning == False and temptouchreading==0: #I'm not turning (so I want to activate us2 pos)
			print "sliding down bit by bit, activate"
			movelimbENC(ARM, BRINGDOWNPOWER, 65)
			movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
			time.sleep(0.7)
		
		#check HIGH US(2) for big thing	
		if takeusreading(US2TRIG, US2ECHO) > US2STANDARD and temptouchreading==0:
			#Nothing detected -> low lying object -> LITTER
			buzz("short"); print "low-lying object detected"; time.sleep(0.5)
			
			#DETECTION CORRECTION PROCEDURES
			#if while turning, turn back a wee until it's in sight!
			##(if this is not enough, turn back until it's in sigh then not, then turn back)
			if alreadyturning == True:
				#turn back way it was turning, while it's not in sight (i.e. until it's in sight)
				turnwhilecondition("turnback", USNEWTRIG, USNEWECHO, ">", USSTANDARD)
				#carry on turning a bit more until it's not in sight
			#	turnwhilecondition("turnback", USNEWTRIG, USNEWECHO, "<", USSTANDARD)
				#shift back - zoning in
			#	if turnycount%2 == 0: movelimbENC(LWHEEL, -TURNPOWER, 50, RWHEEL, TURNPOWER)
			#	else:                 movelimbENC(RWHEEL, -TURNPOWER, 50, LWHEEL, TURNPOWER)				
			
			#if not turning, turn left till nothing there, turn right till nothing there, then shift left a wee.
			#this zones in on the litter, wherever it is.
			else:
				#turn in a direction, until it's out of sight
				turnwhilecondition("notturnback", USNEWTRIG, USNEWECHO, "<", USSTANDARD)
				#turn back in the other direction, until it's out of sight
				turnwhilecondition("turnback",    USNEWTRIG, USNEWECHO, "<", USSTANDARD)
				#shift a bit back; this centres John on the litter.
				if turnycount%2 == 0: movelimbENC(LWHEEL, -TURNPOWER, 50, RWHEEL, TURNPOWER)
				else:                 movelimbENC(RWHEEL, -TURNPOWER, 50, LWHEEL, TURNPOWER)					
			
			#shooby closer/further if litter is not in optimum range to pick up
			shoobied = 'no'
			if tempreading <= OPTLITTERRANGE[0]: #too close
				print "too close, shoobying AWAY"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
				shoobied='away'
			elif tempreading >= OPTLITTERRANGE[1]: #too far
				print "too far, shoobying NEAR"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
				shoobied='near'
			
			#PICK UP THE BLOODY LITTER
			pickprocedure()
			
			#move back if shoobied before
			if shoobied=='away':
				print "shoobying NEAR back to original pos"
				movelimbENC(LWHEEL, WHEELPOWER, 160, RWHEEL, WHEELPOWER)
			elif shoobied=='near':
				print "shoobying AWAY back to original pos"
				movelimbENC(LWHEEL, -WHEELPOWER, 160, RWHEEL, -WHEELPOWER)
			
			#turn back to correct turnbear
			if alreadyturning == False:
				pass
				#is this necessary??
		
		else:
			#Something detected -> tall object -> WALL
			print "WALL"; buzz("long") #WALL(either by US or touch)
			
			if alreadyturning == False: #I'm not turning already so I want to turn and deactivate at wall
				turnprocedure()
			
				#bring us2 back up (deactivate)
				print "sliding up, deactivate"
				movelimbLENG(ARM, SLIDEUPPOWER, 0.6)
				#loop back and carry on
			
			elif alreadyturning == True: #I am already turning so I want to get away from this goddamn wall
				print "turning away from goddamn wall"
				#turn until wall is no longer in sight (to get rid of stalling problem)(screw detection)
				turnwhilecondition("notturnback", US2TRIG, US2ECHO, "<=", US2STANDARD)
								
def restartprogram(channel=0): #debounce interrupt, restart program
	global debouncetimestamp
	timenow = time.time()
	
	#handle button being pressed when main is running - restart (essentially, stop)
	if timenow - debouncetimestamp >= 0.3: #debounce ir so only 1 interrupt
		print "taking action on interrupt"
		if startmain == True: #only restart program if main is actually running!
			BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0; drivewheels(0,0) #stop all
			buzz("short long"); GPIO.cleanup()
			print "Stop pressed - Restarting program"
			os.execl(sys.executable, sys.executable, *sys.argv) #restart
	debouncetimestamp = timenow

#set GPIO interrupts
GPIO.add_event_detect(IRRCINT, GPIO.RISING, callback=restartprogram) #stop program when interrupted!



################
##MAIN PROGRAM##
################
buzz("short"); print "I'm ready to go!"

startmain = False
while True:
	try: #handle ctrl-c to ensure clean exit
		clock.tick(10) #make sure constant FPS so John doesn't blow up
		
		#infrared remote control handling loop
		ircode = lirc.nextcode()
		if ircode:
			fwdb=0
			#buttons to start main program in various directions
			if ircode[0]  ==  "startmainfwdleft":  #pressed 1
				turnycount = 1 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0] == "startmainfwdright": #pressed 2
				turnycount = 0 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0] == "startmainbwdleft":  #pressed 4
				turnycount = 1 ; fwdb = origfwdb + 180.0 ; buzz("short short")
				startmain = True; time.sleep(2)
			elif ircode[0] == "startmainbwdright": #pressed 5
				turnycount = 0 ; fwdb = origfwdb + 180.0 ; buzz("short short")
				startmain = True; time.sleep(2)
			
			#buttons to handle other things
			elif ircode[0] == "startshutdown":     #pressed 0
				print "Shutting down!"; buzz("short short short short")
				os.system('sudo shutdown -h now')
			elif ircode[0] == "startcmpautocalib": #pressed SETUP
				#start calibration procedure of compass
				print "starting calibration script"; buzz("long long")
				cmpautocalib.maincalibprogram()
				os.execl(sys.executable, sys.executable, *sys.argv) #restart to reset all GPIO pins
			elif ircode[0] == "startstopev":       #pressed 7
				#stop getty (if it didn't stop at boot)
				print "deactivating getty" ; buzz("long short")
				os.system("sudo ./stopev.sh") ; print "restarting"
				GPIO.cleanup(); os.execl(sys.executable, sys.executable, *sys.argv)
			elif ircode[0] == "stopmainpy":        #pressed 9
				#stop main.py program (for diagnostics)
				print "stopping main"; buzz("long long long")
				GPIO.cleanup(); sys.exit()
			elif ircode[0] == "bants":             #pressed PLAY
				buzz("long long short short long short short short long short short")
			
			if fwdb > 360.0: fwdb -= 360.0 #correction
			print turnycount, fwdb
		

		
		if startmain == True:

			print "main has started"
			#initial stuff
			turnbears = createturnbears()
			
			#bring arm back up and open grabber in case it's not
			movelimbLENG(ARM, SLIDEUPPOWER, 0.3, GRABBER, OPENPOWER)

			#initial turn from forwards
			turnprocedure()

			#MAIN MAIN CHOW MEIN LOOP
			while True:
				try:
					#stop actions
					BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0

					#drive
					drivewheels(WHEELPOWER, WHEELPOWER)

					#search for object
					detectprocedure(False)

					#check IR sensor for cliff
					if GPIO.input(IRIN) == 1: #nothing close (underneath sensor)
						print "CLIFF"
						#reverse!
						movelimbENC(LWHEEL, -WHEELPOWER, 130, RWHEEL, -WHEELPOWER)
						
						buzz("long")
						turnprocedure()
						#loop back and carry on

				except KeyboardInterrupt: #ensure clean exit
					GPIO.cleanup()
					sys.exit()

	except KeyboardInterrupt: #ensure clean exit
		GPIO.cleanup()
		sys.exit()
