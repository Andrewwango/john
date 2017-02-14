print "SATATR"

import os, sys, time
i=0

while 1:
	print i
	i+=1
	time.sleep(0.5)
	if i==10:
		os.execl(sys.executable, sys.executable, *sys.argv)
