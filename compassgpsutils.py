import smbus, gps, time, math

#compass setup
bus = smbus.SMBus(1)
address = 0x1e
x_offset = -17
y_offset = -300
scale=0.92

#gps setup
def gpssetup():
	# Listen on port 2947 (gpsd) of localhost
	session = gps.gps("localhost", "2947")
	session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
	return session

#compass setup funcs
def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def write_byte(adr, value):
    bus.write_byte_data(address, adr, value)
   
write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000) # Continuous sampling

def takebearing():
	x_out = (read_word_2c(3) - x_offset) * scale
	y_out = (read_word_2c(7) - y_offset) * scale
	z_out = (read_word_2c(5)) * scale

	bearing  = math.atan2(y_out, x_out) 
	if (bearing < 0):
		bearing += 2 * math.pi

	print "Bearing: ", math.degrees(bearing)
	return math.degrees(bearing)

def getGPScoords(sesh):
	try:
		report = sesh.next()
		# Wait for a 'TPV' report and display the current coods
		#print report
		if report['class'] == 'TPV':
			if hasattr(report, 'lon'):
				if hasattr(report, 'lat'):
					coordsout = [float(report.lat),float(report.lon)]
					return coordsout
	except KeyError:
		pass
	except KeyboardInterrupt:
		quit()
	except StopIteration:
		sesh = None
		print "GPSD has terminated"

