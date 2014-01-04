##
## a class for turning on an SSR
##
#import RPi.GPIO as GPIO
import wiringpi
import time
from pprint import pprint
#from threading import Thread
import threading
from subprocess import call

class SSR(threading.Thread):
	def __init__(self, ssr):
		self.ssr = ssr
		
		threading.Thread.__init__(self)
		#wiringPiSetupSys
		#wiringpi.wiringPiSetupGpio()
		
		# set up the pin in out mode
		call(["/usr/local/bin/gpio", "mode", str(ssr.pin), "out"])
		wiringpi.wiringPiSetupSys()
		wiringpi.pinMode(ssr.pin,1)
		
		self.daemon = True
		self.duty_cycle = 0
		self.cycle_time = 0
		self.power = 100
		self.enabled = False
		self._On = False
		
		self.verbose = True
		
		#create an event so we can stop
		self._stop = threading.Event()
	
	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()
	
	def setEnabled(self, enabled):
		if self.verbose:
			print "Enabled: " + str(enabled) + " on pin: " + str(self.ssr.pin)
		self.enabled = enabled
		
		if not enabled:
			self.setState(False)
			
	def isEnabled(self):
		return self.enabled	
	
	def run(self):
		while not self.stopped():
			if self.enabled:
				self.fireSSR()
			else:
				self.setState(False)
				time.sleep(2)
		
		self.setState(False)

	def getonofftime(self, cycle_time, duty_cycle):
		duty = duty_cycle/100.0
		on_time = cycle_time*(duty)
		off_time = cycle_time*(1.0-duty)   
		return [on_time, off_time]
		
	#updates the duty/cycle time
	def updateSSR(self, duty_cycle, cycle_time):
		if self.duty_cycle != duty_cycle or self.cycle_time != cycle_time:
			self.duty_cycle = duty_cycle
			self.cycle_time = cycle_time
							
	def fireSSR(self):
		#self.duty_cycle = duty_cycle;
		if self.verbose:
			print "Fire: " + str(self.enabled) + " " + str(self.ssr.pin) + " " + str(self.power) + " " + str(self.duty_cycle) + " " + str(self.cycle_time)
		
		if self.power < 100 or self.duty_cycle < 100:
			if self.power < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.power)
			elif self.duty_cycle < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.duty_cycle)

			if (on_time > 0):
				if self.verbose:
					print str(self.ssr.pin) + " ON for: " + str(on_time)
				
				self.setState(True)
				time.sleep(on_time)
		
			self.setState(False)
			time.sleep(off_time)
		elif self.duty_cycle == 100:
			self.setState(True)
			time.sleep(self.cycle_time)	
		else:
			self.setState(False)
			time.sleep(self.cycle_time)			


	#sets the power for this ssr from 1-100
	def setPower(self, newpower):
		self.power = float(newpower)
		
	#get the power for this ssr from 1-100
	def getPower(self):
		return float(self.power);
		
	def getState(self):
		ret=0
		if self._On:
			if self.verbose:
				print str(self.ssr.pin) + " ON"
			ret=1
		else:
			if self.verbose:
				print str(self.ssr.pin) + " OFF"
				
		wiringpi.digitalWrite(self.ssr.pin,ret)
		
		return ret
		
	def setState(self, state):
		self._On = state
		if self.ssr.state != state:
			self.ssr.state = state
			self.ssr.save()