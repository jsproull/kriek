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

		#print ssr.name + " update_ssr current " + str(settemp) + " : " + str(target_temp) + " " + str(ssr.pid.power)

		self.set_enabled(enabled)

		# we don't have to do anything
		if ssr.manual_mode:
			return

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
		self.ssr = SSR.objects.get(pk=self.ssr.pk)

		if self.verbose:
			print str(self.ssr.name) + " set_enabled: " + str(enabled) + " on pin: " + str(self.ssr.pin)
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
			print self.ssr.name + " Fire: self.enabled:" + str(self.enabled) + " ssr.enabled: " + str(self.ssr.enabled) + " pid enabled:" + str(self.ssr.pid.enabled)
			print self.ssr.name + " pin:" + str(self.ssr.pin) + " power:" + str(self.power) + " dc:" + str(self.duty_cycle)
			print self.ssr.name + " ct:" + str(self.cycle_time)

		#special case for pwm mode
		# todo, incorporate this in set_state
		if self.ssr.pwm_mode:
			#the ssr name has to be something like ocp.3/pwm_test_P9_42.16

			dir = "/sys/devices/" + self.ssr.pin

			try:
				if self.enabled:
					file = open(dir + "/run", "w")
					file.write("1")
					file.close()

					period = int(self.ssr.pid.cycle_time*1000000000)

					duty = period*self.ssr.pid.power/100
					duty = int(period-duty) #duty is reversed
					file = open(dir + "/duty", "w")
					file.write(str(duty))
					file.close()

					file = open(dir + "/period", "w")
					file.write(str(period))
					file.close()

				else:
					file = open(dir + "/run", "w")
					file.write("0")
					file.close()

			except IOError:
				print "can't open file in " + dir

			#only check if we have to modify this setting every 5 seconds
			time.sleep(5)

			return

		#just return if not enabled
		if not self.enabled:
			self.set_state(False)
			time.sleep(self.cycle_time)
			return

		on_time = 0
		off_time = 0

		# if the ssr is in manual mode, the user turns it on/off by the 'enabled' propery
		if self.ssr.manual_mode:
			self.set_state(self.ssr.enabled)
			return

		# if the pid and the ssr are both enabled, use the PID algorithm
		elif self.ssr.pid.enabled and self.ssr.enabled:
			if self.verbose:
				print " pid enabled.. setting on/off time"

			if self.power < 100:
				on_time, off_time = self.getonofftime(self.cycle_time, self.power)
			else:
				on_time, off_time = self.getonofftime(self.cycle_time, self.duty_cycle)

			if self.verbose:
				print " " + str(self.ssr.pin) + " ON for: " + str(on_time) + " OFF for: " + str(off_time)

			if on_time > 0:
				self.set_state(True)
				time.sleep(on_time)
		
			if off_time > 0:
				self.set_state(False)
				time.sleep(off_time)

		# else if the pid is disabled, but the ssr is enabled
		elif not self.ssr.pid.enabled and self.ssr.enabled:

			on_time = float(self.cycle_time) * float(self.power)/100
			off_time = self.cycle_time - on_time;
	
			if self.verbose:
				print " pid disabled.. setting on/off time"
				print " " + str(on_time) + " " + str(off_time)

			if on_time > 0:
				self.set_state(True)
				time.sleep(on_time)

			if off_time > 0:
				self.set_state(False)
				time.sleep(off_time)
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
			print str(self.ssr.name) + " digitalWrite: " + str(self.ssr.pin) + " " + str(_state)
		
		if wiringpi_available:
			wiringpi.digitalWrite(self.ssr.pin, _state)

		elif bbb_available:
			if _state:
				GPIO.output(self.ssr.pin, GPIO.HIGH)
			else:
				GPIO.output(self.ssr.pin, GPIO.LOW)

		if self.ssr.state != state:
			self.ssr.state = state
			self.ssr.save()
