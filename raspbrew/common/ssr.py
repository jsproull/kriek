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

#from threading import Thread
import threading
from subprocess import call
from raspbrew.common.models import SSR
import common.pidpy as PIDController

class SSRController(threading.Thread):
	def __init__(self, ssr):
		
		self.verbose = False
		
		self.ssr = ssr
		
		threading.Thread.__init__(self)
		
		# set up the pin in out mode
		if wiringpi_available:
			#call(["/usr/local/bin/gpio", "mode", str(ssr.pin), "out"])
			#wiringpi.wiringPiSetupSys()
			
			#rasp numbering
			wiringpi.wiringPiSetup()
			
			#gpio numbering
			#wiringpi.wiringPiSetupGpio()
			
			#set the pinmode
			wiringpi.pinMode(ssr.pin,1)
		
		self.daemon = True
		self.duty_cycle = 0
		self.cycle_time = 0
		self.power = 100
		self.enabled = False
		self._On = False
		
		self.pid_controller=PIDController.pidpy(ssr.pid)
		
		#create an event so we can stop
		self._stop = threading.Event()

	#updates this controller with a settemp/targettemp and includes an enabled override
	def updateSSRController(self, setTemp, targetTemp, enabled=True):
		ssr=self.ssr
		
		#print "current " + str(setTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
		self.setEnabled(enabled)
		power=ssr.pid.power
		cycle_time=ssr.pid.cycle_time 

		#if the pid isn't enabled, set the power to 100%, but still use its cycletime
		if not ssr.pid.enabled:
			power=100
			cycle_time=100
			self.updateSSR(power, cycle_time)
		else:	
			if ssr.pid.power < 100 or not ssr.pid.enabled:
				self.updateSSR(power, cycle_time)
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

			#update the ssr object
			self.ssr=SSR.objects.get(pk=self.ssr.pk)

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

		if self.ssr.enabled and (self.power < 100 or self.duty_cycle < 100):
			if self.power < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.power)
			elif self.duty_cycle < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.duty_cycle)
			elif not self.ssr.pid.enabled:
				on_time=1
				off_time=0

			if (on_time > 0):
				if self.verbose:
					print str(self.ssr.pin) + " ON for: " + str(on_time)
				
				self.setState(True)
				time.sleep(on_time)
		
			if (off_time > 0):
				self.setState(False)
				time.sleep(off_time)
		elif self.ssr.enabled and self.duty_cycle == 100:
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
			ret=1

				
		return ret
		
	def setState(self, state):
		self._On = state
		_state=0
		if state == True:
			_state=1
				
		if self.verbose:
			print "digitalWrite: " + str(self.ssr.pin) + " " + str(_state)
		
		if wiringpi_available:
			wiringpi.digitalWrite(self.ssr.pin,_state)
			
		if self.ssr.state != state:
			self.ssr.state = state
			self.ssr.save()
