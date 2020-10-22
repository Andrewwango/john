#!/usr/bin/env python2.7

'''
Shutdown script to be activated via hard button to shutdown Pi (instead of via SSH).
A corresponding launcher .sh file is in /home/pi and launches this on boot.
'''

import os, time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

SHUTBUTT = 9
BUZZOUT = 7
GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)

#wait for button to be pressed
GPIO.wait_for_edge(SHUTBUTT, GPIO.FALLING)

#check if held or not
time.sleep(2)

#resetup in case it has been cleaned
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZOUT , GPIO.OUT)
GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)

state = GPIO.input(SHUTBUTT)

print "Shutbutt pressed!"
for i in range(state+4):
	GPIO.output(BUZZOUT, True)
	time.sleep(0.1)
	GPIO.output(BUZZOUT, False)
	time.sleep(0.2)
	
GPIO.cleanup()

if state == 0: #button still held
	print "BUTTON HELD: SHUTTING DOWN"
	os.system("sudo shutdown -h now")
elif state == 1: #button pressed and released
	print "BUTTON PRESSED: REBOOTING"
	os.system("sudo reboot")
