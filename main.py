#!/usr/bin/env python2.7
###################################################
#//JOHN (fully automated roadside litter picker)//#
#                    //main.py//                  #
#         //Started 29.05.16//v15//06.03.17       #
#                //ANDREW WANG//                  #
#            //All Rights Reserved//              #
# //BrickPi: github.com/DexterInd/BrickPi_Python//#
###################################################
#v14 makes new detection correction.

#Import relevant modules
import time, math, lirc, sys, pygame, os, cmpautocalib, logging
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

#Constants
XDEGREES       = 90   #angle between robot path and path (in degs)(INT)
USSTANDARD     = 30   #low us(new) sensor detection threshold
US2STANDARD    = 50   #high us(2) detection threshold
OPTLITTERRANGE = [19,28]#the opt us distance range from which it can pick up stuff
STOPRANGE      = 15   #the allowable range for turnbear (compass)
SHIFTENC       = 30

#Extract FWDB (forward bearing) and BATTERYSAVING data from settings file
settingsfile = open('/home/pi/mainsettings.dat','r')
settingsdata = settingsfile.read().split('\n')
origfwdb = int(float(settingsdata[2])) #origfwdb may be modified for fwdb if going backwards, for example
batterysaving = int(settingsdata[3])
settingsfile.close()
print 'origfwdb ', origfwdb
print 'batterysaving ', batterysaving

#Motor Power Constants
if batterysaving   == 0: extrajuice = 0
elif batterysaving == 1: extrajuice = 20
elif batterysaving == 2: extrajuice = 50
#make sure nothing goes over 255 - highest extrajuice!
WHEELPOWER     = -(190 + extrajuice) #driving power
TURNPOWER      =   170 + extrajuice  #pos = forwards (for ease of use but not technically correct)
SHIFTPOWER     =   160 + extrajuice  #'
BRAKEPOWER     =   -5                #"
SHOOBYPOWER    = -(100 + extrajuice)
GRABBERPOWER   = -(170 + extrajuice)
OPENPOWER      =   70  + extrajuice
LIFTPOWER      = -(200 + extrajuice)
SLIDEUPPOWER   = -(100 + extrajuice) #deactivating arm
BRINGDOWNPOWER =   150 + extrajuice
ACTIVATEUS2POWER=  150
BRINGDOWNBRAKEPOWER = -5

	

##SETUP## motors, sensors, GPIO Pins
BrickPi.MotorEnable[GRABBER] = 1 ; BrickPi.MotorEnable[ARM]    = 1
BrickPi.MotorEnable[LWHEEL]  = 1 ; BrickPi.MotorEnable[RWHEEL] = 1

def restart(): os.execl(sys.executable, sys.executable, *sys.argv)
try: #catch error if getty wasn't disabled on boot
	BrickPiSetupSensors()
except OSError:
	print "Getty not disabled"
	os.system("sudo sh /home/pi/stopev.sh")
	restart()

GPIO.setup(IRIN     , GPIO.IN)  ; GPIO.setup(BUZZOUT , GPIO.OUT)
GPIO.setup(USNEWECHO, GPIO.IN)
GPIO.setup(USNEWTRIG, GPIO.OUT)
GPIO.setup(US2ECHO  , GPIO.IN)
GPIO.setup(US2TRIG  , GPIO.OUT) ; GPIO.setup(IRRCINT , GPIO.IN)

##PROGRAM VARS##
turnycount = 0 #first turn is left(1) or right (0) (INCLUDING initial)
turnbears = []
targBear = 0
shoobied = 'no'
debouncetimestamp = time.time()

#Setup logging
logging.basicConfig(filename='/home/pi/errorlogs.dat', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logging.debug('\n \n ---NEW SESSION---')

print "SETUP FINISHED"

#############
##FUNCTIONS##
#############

try:
	def buzz(patternofbuzz): #activate buzzer
		patternofbuzz = patternofbuzz.split()
		for i in range(len(patternofbuzz)):
			GPIO.output(BUZZOUT, True)
			if   patternofbuzz[i] == "short" : time.sleep(0.1)
			elif patternofbuzz[i] == "long"  : time.sleep(0.3)
			GPIO.output(BUZZOUT, False)
			if len(patternofbuzz) >= 1 and i != len(patternofbuzz)-1: time.sleep(0.2) #if more than one beep and not at end

	def takeusreading(trig, echo, repeats=3, disregardhigh=False): #take reading from ultrasonic sensor
		GPIO.output(trig, False) #switch everything off
		#take 4 readings then find average
		uslist=[]
		for i in range(repeats):
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
			if distance > 5000 and disregardhigh == True:
				pass
			else:	
				uslist += [int(distance)]
			time.sleep(0.01)
		uslist.sort(); usreading = uslist[repeats/2] #median (get rid of anomalies)
		GPIO.output(trig, False)
		print "US reading is ", str(usreading), uslist
		return usreading

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
		time.sleep(0.5)
		
		print "opening" #dump litter
		movelimbLENG(GRABBER, OPENPOWER, 0.5); time.sleep(0.5)	

	def turnprocedure(): #TURNING PROCEDURE
		global turnycount; global turnbears; global targBear
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

	def movewhilecondition(formofmovement, trig, echo, op, val, power, wallprevention=False, timelimit=False, llote=False):
		time.sleep(0.4)
		wheel1power,wheel2power = -1,1 #for turning
		b = 0
		if   formofmovement == "turnback":    b = 1
		elif formofmovement == "notturnback": b = 0
		elif formofmovement == "forwards": wheel1power,wheel2power = 1,1 #modify for driving
		elif formofmovement == "backwards":wheel1power,wheel2power = -1,-1
		#set wheel directions
		if turnycount%2 == b: #direction is inputted by user
			wheel1 = LWHEEL; wheel2 = RWHEEL
		else:
			wheel1 = RWHEEL; wheel2 = LWHEEL
		
		if llote == True: string = "takeusreading(trig, echo, repeats=1)" #don't repeat readings
		else: string = "takeusreading(trig, echo)"
		ot = time.time()
		while eval(string + op + "val"):
			if wallprevention == True:
				#just stop turning when there's a wall no matter what, if necessary
				if takeusreading(US2TRIG, US2ECHO) < US2STANDARD:
					break
			if time.time()-ot >= 1:
				break
			#turn until condition is met
			BrickPi.MotorSpeed[wheel1] = wheel1power*power; BrickPi.MotorSpeed[wheel2] = wheel2power*power
			BrickPiUpdateValues()

		movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake
		drivewheels(0,0) #stop
		time.sleep(0.4)

	def detectprocedure(alreadyturning): #DETECTION PROCEDURE

		#check LOW US for object
		tempreading = takeusreading(USNEWTRIG,USNEWECHO)
		if tempreading < USSTANDARD:
			#detected something!
			drivewheels(0,0) #stop
			print "object detected"; buzz("long")

			#activate HIGH US(2) pos
			if alreadyturning == False: #I'm not turning (so I want to activate us2 pos)
				print "sliding down bit by bit, activate"
				movelimbENC(ARM, ACTIVATEUS2POWER, 70)
				movelimbLENG(ARM, BRINGDOWNBRAKEPOWER, 0.1) #brake to prevent coast
				time.sleep(0.7)

			#check HIGH US(2) for big thing	
			if takeusreading(US2TRIG, US2ECHO) > US2STANDARD:
				#Nothing detected -> low lying object -> LITTER
				buzz("short"); print "low-lying object detected"; time.sleep(0.5)

				#DETECTION CORRECTION PROCEDURES
				#if while turning, turn back a wee until it's in sight!
				##(if this is not enough, turn back until it's in sight then not, then turn back)
				messedup = True
				if alreadyturning == True:
					for i in range(2):
						#turn back way it was turning, while it's not in sight (i.e. until it's in sight)
						print "turn back until in sight"
						movewhilecondition("turnback", USNEWTRIG, USNEWECHO, ">", USSTANDARD, SHIFTPOWER, timelimit=True, llote=True)
						print "turn not back until out of sight"
						movewhilecondition("notturnback", USNEWTRIG, USNEWECHO, "<", USSTANDARD, SHIFTPOWER, llote=True)
						#print "turn not back until out of sight"
						#movewhilecondition("notturnback", USNEWTRIG, USNEWECHO, "<", USSTANDARD, SHIFTPOWER)
						print "turn back until in sight"
						movewhilecondition("turnback", USNEWTRIG, USNEWECHO, ">", USSTANDARD, SHIFTPOWER, timelimit=True, llote=True)
						messedup = False
						#in case it's monumentally messed up, turn back!
						if takeusreading(USNEWTRIG,USNEWECHO) > USSTANDARD: #monumentally messed up
							print "turning back, cos monumentally failed"
							movewhilecondition("notturnback", USNEWTRIG, USNEWECHO, ">", USSTANDARD, SHIFTPOWER, timelimit=True)
							messedup = True
						
						if messedup == False: break

				#if not turning, turn direction A until out of sight, turn away in dir B until in sight,
				#then carry on in B until out of sight, then back in A until in sight again (this centres it!)
				else:
					#turn in a direction, until it's out of sight
					print "Turning direction until no longer in sight"
					movewhilecondition("notturnback", USNEWTRIG, USNEWECHO, "<", USSTANDARD, SHIFTPOWER, wallprevention=True, llote=True)
					#turn back in the other direction until it's in sight again
					print "Turning other direction until in sight again"
					movewhilecondition("turnback",    USNEWTRIG, USNEWECHO, ">", USSTANDARD, SHIFTPOWER, timelimit=True, llote=True)
					#carry on, until it's out of sight
					print "Turning other direction until no longer in sight"
					movewhilecondition("turnback",    USNEWTRIG, USNEWECHO, "<", USSTANDARD, SHIFTPOWER, wallprevention=True, llote=True)
					#shift a bit back; this centres John on the litter.
					#print "shift"
					#if turnycount%2 == 0: movelimbENC(LWHEEL, -TURNPOWER, SHIFTENC, RWHEEL, TURNPOWER)
					#else:                 movelimbENC(RWHEEL, -TURNPOWER, SHIFTENC, LWHEEL, TURNPOWER)
					#turn in original direction until it's in sight - now it's definitely in sight.
					print "Turning in orginial direction to centre"
					movewhilecondition("notturnback", USNEWTRIG, USNEWECHO, ">", USSTANDARD, SHIFTPOWER, timelimit=True, llote=True)

				#shooby closer/further if litter is not in optimum range to pick up
				shoobied = 'no'; print "checking shooby"
				tempreading = takeusreading(USNEWTRIG, USNEWECHO, repeats=7, disregardhigh=True)
				startpos = takeencoderreading(LWHEEL)
				if tempreading <= OPTLITTERRANGE[0]: #too close
					print "too close, shoobying AWAY"
					movewhilecondition("backwards", USNEWTRIG, USNEWECHO, "<", OPTLITTERRANGE[0], WHEELPOWER, timelimit=True)
					shoobiedenc = abs(takeencoderreading(LWHEEL) - startpos) #so we know where we've gone
					shoobied='away'
				elif tempreading >= OPTLITTERRANGE[1]: #too far
					print "too far, shoobying NEAR"
					movewhilecondition("forwards",  USNEWTRIG, USNEWECHO, ">", OPTLITTERRANGE[1], WHEELPOWER, timelimit=True)
					shoobiedenc = abs(takeencoderreading(LWHEEL) - startpos)
					shoobied='near'

				#PICK UP THE BLOODY LITTER
				pickprocedure()

				#move back if shoobied before
				if shoobied=='away':
					print "shoobying NEAR back to original pos"
					movelimbENC(LWHEEL, WHEELPOWER, shoobiedenc, RWHEEL, WHEELPOWER)
				elif shoobied=='near':
					print "shoobying AWAY back to original pos"
					movelimbENC(LWHEEL, -WHEELPOWER, shoobiedenc, RWHEEL, -WHEELPOWER)

				#turn back to original turnbear
				if alreadyturning == False:
					adjust = targBear - takebearing()
					#check which direction to turn back (depending on sign of adjust, or if it's wrapping)
					if adjust < 0 or adjust > 180: #turn left
						wheel1 = RWHEEL; wheel2 = LWHEEL
					if adjust > 0 or adjust < 180: #turn right
						wheel1 = LWHEEL; wheel2 = RWHEEL
					print "turning back to original bear"
					movelimbENC(wheel1, -TURNPOWER, targBear, wheel2, TURNPOWER, compass=True)
					movelimbLENG(wheel1, BRAKEPOWER, 0.1, wheel2, -BRAKEPOWER) #brake


			else:
				#Something detected -> tall object -> WALL
				print "WALL"; buzz("long") #WALL(US)

				if alreadyturning == False: #I'm not turning already so I want to turn and deactivate at wall
					turnprocedure()

					#bring us2 back up (deactivate)
					print "sliding up, deactivate"
					movelimbLENG(ARM, SLIDEUPPOWER, 0.6)
					#loop back and carry on

				elif alreadyturning == True: #I am already turning so I want to get away from this goddamn wall
					print "turning away from goddamn wall"
					#turn until wall is no longer in sight (to get rid of stalling problem)(screw detection)
					movewhilecondition("notturnback", US2TRIG, US2ECHO, "<=", US2STANDARD, TURNPOWER)

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
				restart()
		debouncetimestamp = timenow

	#set GPIO interrupts
	GPIO.add_event_detect(IRRCINT, GPIO.RISING, callback=restartprogram) #stop program when interrupted!



	################
	##MAIN PROGRAM##
	################
	buzz("short"); print "I'm ready to go!"

	startmain = False
	while True:
		clock.tick(10) #make sure constant FPS so John doesn't blow up

		#infrared remote control handling loop
		ircode = lirc.nextcode()
		if ircode:
			fwdb=0
			#buttons to start main program in various directions
			if ircode[0]  ==  "startmainfwdleft":  #pressed 1
				turnycount = 1 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(0.3)
			elif ircode[0] == "startmainfwdright": #pressed 2
				turnycount = 0 ; fwdb = origfwdb; buzz("short short")
				startmain = True; time.sleep(0.3)
			elif ircode[0] == "startmainbwdleft":  #pressed 4
				turnycount = 1 ; fwdb = origfwdb + 180 ; buzz("short short")
				startmain = True; time.sleep(0.3)
			elif ircode[0] == "startmainbwdright": #pressed 5
				turnycount = 0 ; fwdb = origfwdb + 180 ; buzz("short short")
				startmain = True; time.sleep(0.3)
			
			#buttons to handle batterysaving changes
			elif ircode[0] in ["batterysavingoff", "batterysavingon", "batterysavingsuper"]:
				if   ircode[0] == "batterysavingoff"  : newbatterysaving = 0
				elif ircode[0] == "batterysavingon"   : newbatterysaving = 1
				elif ircode[0] == "batterysavingsuper": newbatterysaving = 2
				
				#read and modify current data
				settingsfile = open('/home/pi/mainsettings.dat','r')
				currentdata = settingsfile.read().strip('\n').split('\n')
				currentdata.pop(-1); currentdata.append(newbatterysaving)
				settingsfile.close()
				
				#write new data
				settingsfile = open('/home/pi/mainsettings.dat','w')
				datatowrite = ""
				for piece in currentdata:
					datatowrite = datatowrite + "\n" + str(piece)
				datatowrite = datatowrite.strip("\n")
				settingsfile.write(datatowrite)
				print "added newbatterysaving", newbatterysaving
				settingsfile.close(); buzz("short"); GPIO.cleanup(); restart()
			
			#buttons to handle other things
			elif ircode[0] == "startshutdown":     #pressed 0
				print "Shutting down!"; buzz("short short short short")
				os.system('sudo shutdown -h now')
			elif ircode[0] == "startcmpautocalib": #pressed SETUP
				#start calibration procedure of compass
				print "starting calibration script"; buzz("long long")
				cmpautocalib.maincalibprogram()
				restart() #restart to reset all GPIO pins
			elif ircode[0] == "startstopev":       #pressed 7
				#stop getty (if it didn't stop at boot)
				print "deactivating getty" ; buzz("long short")
				os.system("sudo ./stopev.sh") ; print "restarting"
				GPIO.cleanup(); restart()
			elif ircode[0] == "stopmainpy":        #pressed 8
				#stop main.py program (for diagnostics)
				print "stopping main"; buzz("long long long")
				GPIO.cleanup(); sys.exit()
			elif ircode[0] == "bants":             #pressed PLAY
				buzz("long long short short long short short short long short short")

			if fwdb > 360: fwdb -= 360 #correction
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
				#stop actions
				#BrickPi.MotorSpeed[GRABBER] = 0; BrickPi.MotorSpeed[ARM] = 0

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

except (KeyboardInterrupt, SystemExit): #ensure clean exit
	logging.exception('KeyboardInterrupt or SystemExit'); print "KeyboardInterrupt or SystemExit"
	GPIO.cleanup(); raise
except: #any other error, restart!
	logging.exception('Found error in main!'); print "Found error in main!"
	GPIO.cleanup(); restart()
