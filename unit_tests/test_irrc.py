'''
Hardware test of the IR remote control unit.
On running, the code of pressed buttons will be printed continously.
'''

import lirc, time

sockid = lirc.init("irrctest",blocking=False)
print("Ready")
i=0
while True:
	i+=1
	print i
	code = lirc.nextcode()
	if code: print(code[0])
	time.sleep(0.5)
