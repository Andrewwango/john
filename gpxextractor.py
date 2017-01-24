import math, os

#import file
gpxfile=open(os.path.join(__location__, 'johntrackreal.gpx'),'r') #see screenshot for 'jtreal'
gpxdata=gpxfile.read().split()
cdp=[] #changedirpoints - [[lat1,lon1,bear1],[lat2,...],...]

def calculateBearing(lat1,lon1,lat2,lon2):
	#calculate bearing between 2 points
	lat1=math.radians(lat1); lat2=math.radians(lat2); deltalon=math.radians(lon2)-math.radians(lon1)
	X=math.cos(lat2)*math.sin(deltalon)
	Y=(math.cos(lat1)*math.sin(lat2))-(math.sin(lat1)*math.cos(lat2)*math.cos(deltalon))
	bearing = math.degrees(math.atan2(X,Y))
	if bearing<0: bearing+=360
	return bearing

def makecdp():
	for i in gpxdata:
		#parse gpx and make array
		if 'lat=' in i:
			ilat=float(i.strip('lat="').strip('"'))
		elif 'lon=' in i:
			ilon=float(i.strip('lon="').strip('">'))
			ibear=0
			cdp.append([ilat, ilon, ibear])
			ilat=0;ilon=0;ibear=0

	for i in range(len(cdp)): #iterate through indices
		if i==(len(cdp)-1):
			#last point
			cdp[i][2]=0 #bearing is meaningless
		else:
			#enter bearing between point and next one
			cdp[i][2]=calculateBearing(cdp[i][0],cdp[i][1],cdp[i+1][0],cdp[i+1][1])
	#cdp[0][0]=0;cdp[0][1]=0 #get rid of initial location
	print cdp
	return cdp

for i in makecdp():
	print i
