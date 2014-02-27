##
## a class for turning on an SSR
##
#import RPi.GPIO as GPIO
try:
	import wiringpi
	wiringpi_available = True
except ImportError:
	wiringpi_available = False

try:
	import Adafruit_BBIO.GPIO as GPIO
	bbb_available = True
except ImportError:
	bbb_available = False


import time

#from threading import Thread
import threading
from kriek.common.models import SSR
import common.pidpy as pid_controller


class SSRController(threading.Thread):
	def __init__(self, ssr):
		
		self.verbose = True
		
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
			wiringpi.pinMode(ssr.pin, 1)
		elif bbb_available:
			GPIO.setup(ssr.pin, GPIO.OUT)
			#GPIO.cleanup()

		self.daemon = True
		self.duty_cycle = 0
		self.cycle_time = 0
		self.power = 100
		self.enabled = False
		self._On = False
		
		self.pid_controller = pid_controller.pidpy(ssr.pid)
		
		#create an event so we can stop
		self._stop = threading.Event()

	#updates this controller with a settemp/targettemp and includes an enabled override
	def update_ssr_controller(self, settemp, target_temp, enabled=True):
		#update the ssr object
		self.ssr = SSR.objects.get(pk=self.ssr.pk)

		ssr = self.ssr

		#print "update_ssr current " + str(settemp) + " : " + str(target_temp) + " " + str(ssr.pid.power)

		self.set_enabled(enabled)
		self.power = ssr.pid.power
		self.cycle_time = ssr.pid.cycle_time

		#if the pid isn't enabled, set the power to 100%, but still use its cycletime
		if not ssr.pid.enabled:
			#self.power = 100
			#self.cycle_time = 1
			self.update_ssr(self.power, self.cycle_time)
		else:	
			if ssr.pid.power < 100:
				self.update_ssr(self.power, self.cycle_time)
			else:
				duty_cycle = self.pid_controller.calcPID_reg4(float(settemp), float(target_temp), True)
				self.update_ssr(duty_cycle, ssr.pid.cycle_time)
		
	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()
	
	def set_enabled(self, enabled):
		if self.verbose:
			print "Enabled: " + str(enabled) + " on pin: " + str(self.ssr.pin)
		self.enabled = enabled
		
		if not enabled:
			self.set_state(False)
			
	def is_enabled(self):
		return self.enabled	
	
	def run(self):
		while not self.stopped():
			self.fire_ssr()

			if not self.enabled:
				time.sleep(2)


		self.set_state(False)

	def getonofftime(self, cycle_time, duty_cycle):
		duty = duty_cycle / 100.0
		on_time = cycle_time * duty
		off_time = cycle_time * (1.0-duty)
		return [on_time, off_time]

	#updates the duty/cycle time
	def update_ssr(self, duty_cycle, cycle_time):
		if self.duty_cycle != duty_cycle or self.cycle_time != cycle_time:
			self.duty_cycle = duty_cycle
			self.cycle_time = cycle_time
							
	def fire_ssr(self):
		#self.duty_cycle = duty_cycle;
		if self.verbose:
			print self.ssr.name
			print " Fire: enabled:" + str(self.enabled) + " pid enabled:" + str(self.ssr.pid.enabled)
			print " pin:" + str(self.ssr.pin) + " power:" + str(self.power) + " dc:" + str(self.duty_cycle)
			print " ct:" + str(self.cycle_time)

		#just return if not enabled
		if not self.enabled:
			self.set_state(False)
			time.sleep(self.cycle_time)			
			return


		on_time = 0
		off_time = 0

		if self.ssr.pid.enabled and self.ssr.enabled and (self.power < 100 or self.duty_cycle < 100):
			if self.verbose:
				print " pid enabled.. setting on/off time"

			if self.power < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.power)
			elif self.duty_cycle < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.duty_cycle)

			if on_time > 0:
				if self.verbose:
					print " " + str(self.ssr.pin) + " ON for: " + str(on_time)
				
				self.set_state(True)
				time.sleep(on_time)
		
			if off_time > 0:
				self.set_state(False)
				time.sleep(off_time)

		elif (not self.ssr.pid.enabled and self.ssr.enabled) or (self.ssr.enabled and self.duty_cycle == 100):

			self.set_state(True)
			on = float(self.cycle_time) * float(self.power)/100
			off = self.cycle_time - on;
	
			if self.verbose:
				print " pid disabled.. setting on/off time"
				print " " + str(on) + " " + str(off)

			time.sleep(on)
			self.set_state(False)
			time.sleep(off)
			
		else:
			self.set_state(False)
			time.sleep(self.cycle_time)			

	#sets the power for this ssr from 1-100
	def set_power(self, newpower):
		self.power = float(newpower)
		
	#get the power for this ssr from 1-100
	def get_power(self):
		return float(self.power)

	def get_state(self):
		ret = 0
		if self._On:
			ret = 1

		return ret
		
	def set_state(self, state):
		self._On = state
		_state = 0
		if state:
			_state = 1
				
		if self.verbose:
			print "digitalWrite: " + str(self.ssr.pin) + " " + str(_state)
		
		if wiringpi_available:
			print "PI"
			wiringpi.digitalWrite(self.ssr.pin, _state)

		elif bbb_available:
			if _state:
				print "HI"
				GPIO.output(self.ssr.pin, GPIO.HIGH)
			else:
				GPIO.output(self.ssr.pin, GPIO.LOW)

		if self.ssr.state != state:
			self.ssr.state = state
			self.ssr.save()
