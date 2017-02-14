import lirc, time

sockid = lirc.init("irrctest",blocking=False)
print("Ready")

while True:
	code = lirc.nextcode()
	if code: print(code[0])
	time.sleep(0.2)
