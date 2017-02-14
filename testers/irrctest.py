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
