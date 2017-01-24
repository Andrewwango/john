import gps, time
#kill gpsd: sudo killall gpsd
#sudo rm /var/run/gpsd.socket
# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
    try:
    	report = session.next()
		# Wait for a 'TPV' report and display the current time
		# To see all report data, uncomment the line below
	#print report
        if report['class'] == 'TPV':
            if hasattr(report, 'lon'):
		if hasattr(report, 'lat'):
                	print str(report.lat) + ", " + str(report. lon)
			time.sleep(0.2)
    except KeyError:
		pass
    except KeyboardInterrupt:
		quit()
    except StopIteration:
		session = None
		print "GPSD has terminated"