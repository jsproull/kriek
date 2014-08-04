#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep 
import time

GPIO.setmode(GPIO.BCM)

INPUT_PIN  = 4
pulseCount = 0
oldTime = 0
flowRate          = 0.0
flowMilliLitres   = 0
calibrationFactor = 4.5

GPIO.setup(INPUT_PIN, GPIO.IN) 

def millis():
	millis = int(round(time.time() * 1000))
	return millis

def inputLow(channel):
	global pulseCount
	#global oldTime, calibrationFactor
	#global flowRate, flowMilliLitres
	pulseCount = pulseCount + 1

def inputHigh(channel):
	global pulseCount
	pulseCount = pulseCount+1
	Calc = (pulseCount * 60 / 7.5);
	print str(Calc) + " L/hour"
	#print str(pulseCount)
	pass

#GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=inputHigh, bouncetime=200)
GPIO.add_event_detect(INPUT_PIN, GPIO.FALLING, callback=inputLow, bouncetime=0)
#GPIO.add_event_detect(INPUT_PIN, GPIO.BOTH, callback=inputHigh, bouncetime=200)

while True: 
	#test = GPIO.input(INPUT_PIN) 
	#Calc = (pulseCount * 60 / 7.5);
	#print str(Calc) + " L/hour"
	#Calc = (pulseCount * 60 / 7.5)

	flowRate = ((1000.0 / (millis() - oldTime)) * pulseCount) / calibrationFactor
	oldTime = millis()
	flowMilliLitres = (flowRate / 60) * 1000
	print str(flowMilliLitres) + " ml/sec"
	#print str(flowRate) + " " + str(pulseCount)
	
	#print "sleep"
	pulseCount = 0
	sleep(1)


