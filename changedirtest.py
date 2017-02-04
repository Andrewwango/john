import time, math, pygame
import gpxextractor, compassgpsutils

XDEGREES=30
clock=pygame.time.Clock()

##PROCESS GPX##
cdp = gpxextractor.makecdp()[:]
currentcdp = cdp[0]
print cdp
print currentcdp

seshvar = compassgpsutils.gpssetup()

#rest of setup

while True:
	
	#create list of bearings for each turn
	turnbears=[currentcdp[2]-XDEGREES,currentcdp[2]+XDEGREES] #l,r
	for i in range(len(turnbears)): #correct to 0<b<360
		if turnbears[i] > 360: turnbears[i] -= 360
		if turnbears[i] < 0  : turnbears[i] += 360
	
	#initturn
	
	looper=0
	#main loop
	while True:
		
		#other drive and detection
		
		looper+=1
		
		#check if routepoint reached
		checker=[]
		if looper==3: #only check once every 3 loops
			looper = 0
			for i in range(3): #reliability
				currentcoords = compassgpsutils.getGPScoords(seshvar)
				print currentcoords
				print 'checkin'+str(i)
				if currentcoords != None:
					#am i at a cdp?
					for point in cdp:
						if abs(point[0]-currentcoords[0])<=0.00003 and abs(point[1]-currentcoords[1])<=0.00003:
							checker+=[point]
				if len(checker) < (i+1):
					#no new point was added, no point in iterating anymore, get out of loop
					break
						
		
		if all(x == checker[0] for x in checker)==True and checker!=[]:
			#CDP reached
			print "cdp"
			currentcdp = checker[0]
			print currentcdp
			while abs(compassgpsutils.takebearing()-currentcdp[2]) > 10.0:
				print "turn more"
				time.sleep(0.7)
			print "cdpb reached"
			cdp.remove(currentcdp)
			time.sleep(1)
			break
		
		clock.tick(10)
			
