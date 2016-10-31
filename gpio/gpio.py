#!/usr/bin/python
import os
import time
import RPi.GPIO as GPIO

buttonPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonPin, GPIO.IN)

prev_input = GPIO.input(buttonPin)

act_vt = 2
os.system("chvt " + str(act_vt))

while True:
	input = GPIO.input(buttonPin)

	if ((not prev_input) and input):
		if (act_vt == 2):
			act_vt = 3

		elif (act_vt == 3):
			act_vt = 2
		
		os.system("chvt " + str(act_vt))
		
		
#		print ("Changed to " + str(act_vt))
	
	prev_input = input

	time.sleep(0.05)

