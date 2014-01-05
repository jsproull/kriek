##
## a class for turning on an SSR
##
#import RPi.GPIO as GPIO
try:
	import wiringpi
	wiringpi_available=True
except ImportError:
	wiringpi_available=False
	
import time
from pprint import pprint
#from threading import Thread
import threading
from subprocess import call

import common.pidpy as PIDController

class SSR(threading.Thread):
	def __init__(self, ssr):
		self.ssr = ssr
		
		threading.Thread.__init__(self)
		# - wiringPiSetupSys
		# - wiringpi.wiringPiSetupGpio()
		
		# set up the pin in out mode
		if wiringpi_available:
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
		
		self.pid_controller=PIDController.pidpy(ssr.pid)
		
		#create an event so we can stop
		self._stop = threading.Event()

	#updates this controller with a settemp/targettemp and includes an enabled override
	def updateSSRController(self, setTemp, targetTemp, enabled=True):
		ssr=self.ssr
		
		print "current " + str(setTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
		self.setEnabled(enabled)
		
		if ssr.pid.power < 100:
			self.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
		else:
			duty_cycle = self.pid_controller.calcPID_reg4(float(setTemp), float(targetTemp), True)
			self.updateSSR(duty_cycle, ssr.pid.cycle_time)
		
			
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
			print "Fire: enabled:" + str(self.enabled) + " pin:" + str(self.ssr.pin) + " power:" + str(self.power) + " dc:" + str(self.duty_cycle) + " ct:" + str(self.cycle_time)
		
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
				
		if wiringpi_available:
				wiringpi.digitalWrite(self.ssr.pin,ret)
			else:
				print "wiring: " + str(self.ssr.pin) + " " + str(ret)
		
		return ret
		
	def setState(self, state):
		self._On = state
		if not state:
			if wiringpi_available:
				wiringpi.digitalWrite(self.ssr.pin,0)
			else:
				print "wiring: " + str(self.ssr.pin) + " off."
							
		if self.ssr.state != state:
			self.ssr.state = state
			self.ssr.save()