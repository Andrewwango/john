#!/usr/bin/env python2.7
#a corresponding launcher .sh file is in /home/pi and launches this on boot.
import os
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

SHUTBUTT = 9
GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)

GPIO.wait_for_edge(SHUTBUTT, GPIO.FALLING)

print "SHUTBUTT PRESSED, SHUTTING DOWN!!"

GPIO.cleanup()

os.system('sudo shutdown -h now')
