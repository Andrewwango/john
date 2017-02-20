#!/usr/bin/env python2.7
#this will be located in /home/pi as an executable .sh
import os
import RPi.GPIO as GPIO
gpio.setmode(GPIO.BCM)

SHUTBUTT = 9
GPIO.setup(SHUTBUTT, GPIO.IN , pull_up_down=GPIO.PUD_UP)

GPIO.wait_for_edge(SHUTBUTT, GPIO.FALLING)

print "SHUTBUTT PRESSED, SHUTTING DOWN!!"

GPIO.cleanup()

os.system('sudo shutdown -h now')
