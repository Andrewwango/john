#!/usr/bin/env python2.7
#a corresponding launcher .sh file is in /home/pi and launches this on boot.
import os, time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

SHUTBUTT = 9
BUZZOUT = 7
GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)

GPIO.wait_for_edge(SHUTBUTT, GPIO.FALLING)

#resetup in case it has been cleaned
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZOUT , GPIO.OUT)

print "SHUTBUTT PRESSED, SHUTTING DOWN!!"
for i in range(4):
	GPIO.output(BUZZOUT, True)
	time.sleep(0.1)
	GPIO.output(BUZZOUT, False)
	time.sleep(0.2)
	

GPIO.cleanup()
os.system('sudo shutdown -h now')
