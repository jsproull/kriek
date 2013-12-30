#!../env-raspbrew/bin/python
import sys, os

##                      _                       
##                     | |                      
##  _ __ __ _ ___ _ __ | |__  _ __ _____      __
## | '__/ _` / __| '_ \| '_ \| '__/ _ \ \ /\ / /
## | | | (_| \__ \ |_) | |_) | | |  __/\ V  V / 
## |_|  \__,_|___/ .__/|_.__/|_|  \___| \_/\_/  
##               | |                            
##               |_|                            
##
##  Fermpi v3.0 
##
##  This class controls a fermentation chamber. It is responsible for reading 2 temp probes and logging both to sqlite.
##  It will also turn on a cooling/heating unit 
##
##  December 26, 2012 - V3.0 for Raspberry Pi
##

#sys.path.insert(0, "/home/pi/raspbrew")

from common.ssr import SSR as ssrController
import common.pidpy as PIDController
from datetime import datetime
import threading
import time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,Status,SSR
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration


#pyro for remote 
#import Pyro4
def unix_time(self, dt):
	epoch = datetime.utcfromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()

def unix_time_millis(self, dt):
	return self.unix_time(dt) * 1000.0
	
class Raspbrew():#threading.Thread):
	"""
	Fermpi main class	
	"""

	def __init__(self):
		
		#threading.Thread.__init__(self)
		#self.daemon = True
		
		self.power_cycle_time=5.0
		
		#a dictionary of ssr controllers
		self.ssrControllers = {}
		
		#a dictionary of pid controllers
		self.pidControllers={}
		
		#create an event so we can stop
		self._stop = threading.Event()
		
	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	#returns true if the probe is a fermentation probe
	def isFermSSR(self, ssr):
		return ssr.get_mode_display() == 'Fermentation Regular' or ssr.get_mode_display() == 'Fermentation Coolbot'
	
	#returns true if the probe is a brewing probe	
	def isBrewSSR(self, ssr):
		return not self.isFermSSR(ssr)
	
	#returns the fermentation fan probe (if any) from the provided fermentation configuration	
	def getProbeByType(self, fermConf, type):
		probes=fermConf.probes.filter(type=type)
		if probes:
			return probes
		else:
			return None
			
	#returns the fermentation fan probe (if any) from the provided fermentation configuration	
	def getFanProbes(self, fermConf):
		return self.getProbeByType(fermConf,5)

	#returns the fermentation wort probe (if any) from the provided fermentation configuration	
	def getWortProbes(self, fermConf):
		return self.getProbeByType(fermConf,3)
			
	#returns an ssr controller for an ssr by its pk
	def getSSRController(self, ssr):
		try:
			s=self.ssrControllers[ssr.pk]
		except KeyError, e:
			 	self.ssrControllers[ssr.pk]=ssrController(ssr)
			 	s=self.ssrControllers[ssr.pk]
			 	
		return s
		
	#returns a pid controller for a pid by its pk
	def getPidController(self, pid):
		try:
			p=self.pidControllers[pid.pk]
		except KeyError, e:
			 	self.pidControllers[pid.pk]=PIDController.pidpy(pid)
			 	p=self.pidControllers[pid.pk]
			 	
		return p

	# ensure all the temperatures are up to date
	def updateTemps(self):
		probes = Probe.objects.all();
		for probe in probes:
			probe.getCurrentTemp()
			
	#
	# called from the main thread to fire the brewing ssrs (if configured)
	#
	def checkBrew(self):
		#do we have any fermentation probes?
		brewConfs = BrewConfiguration.objects.all();
					
		for brewConf in brewConfs:
			for ssr in brewConf.ssrs.all():
				currentTemp=ssr.probe.getCurrentTemp()
				targetTemp=ssr.probe.target_temperature
				
				ssr_controller=self.getSSRController(ssr)
				pid_controller=self.getPidController(ssr.pid)
				enabled = (targetTemp != None and currentTemp > -999) and (brewConf.allow_multiple_ssrs == True or (brewConf.allow_multiple_ssrs == False and brewConf.current_ssr == ssr))
				
				if enabled:
					#print "current " + str(currentTemp) + " : " + str(targetTemp) + " " + str(ssr_controller.getPower())
					ssr_controller.setEnabled(currentTemp < targetTemp)
					if ssr_controller.getPower() < 100:
						if currentTemp < targetTemp:
							ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
					else:
						duty_cycle = pid_controller.calcPID_reg4(float(currentTemp), float(targetTemp), True)
						ssr_controller.updateSSR(duty_cycle, self.power_cycle_time)
				else:
					ssr_controller.setEnabled(False)
				
	#
	# called from the main thread to fire the brewing ferm (if configured)
	#	
	def checkFerm(self):
		#do we have any fermentation probes?
		fermConfs = FermConfiguration.objects.all();
		
		for fermConf in fermConfs:
			wortProbes=self.getWortProbes(fermConf)
			
			if not wortProbes:
				print "Error: You need at least one Wort probe to run in any fermentation mode."
			
			for wortProbe in wortProbes:	
				wortTemp=wortProbe.getCurrentTemp()
				ssrs=wortProbe.ssr_set.all()
				
				for ssr in ssrs:
					ssr_controller=self.getSSRController(ssr)
					probe = ssr.probe
					targetTemp = probe.target_temperature
					if wortTemp == -999 or targetTemp == None:
						continue
						
					if fermConf.mode == 0: # regular mode
				
						if float(wortTemp) < float(targetTemp):
							ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
							ssr_controller.setEnabled(ssr.heater_or_chiller == 0) #Heater
						elif float(wortTemp) > float(targetTemp):
							ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
							ssr_controller.setEnabled(ssr.heater_or_chiller == 1) #chiller
						else:
							ssr_controller.setEnabled(False);
						
					elif fermConf.mode == 1: # chiller
				
						fanProbes=self.getFanProbes(fermConf)
						if not fanProbes:
							print "Error: You need at least one AC Fan probe to run in 'coolbot' fermentation mode."
							
						for fanProbe in fanProbes:	
							fanTemp=fanProbe.getCurrentTemp()
							
							if ssr.heater_or_chiller == 0: #heater
								if float(wortTemp) > float(targetTemp):
									ssr_controller.setEnabled(True) # enable all ssrs (heater and chiller side)
									ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
								elif float(wortTemp) < float(targetTemp):
									ssr_controller.setEnabled(False);
						
							if float(fanTemp) > -999 and ssr.heater_or_chiller == 0: #heater
 								#if the fan coils are too cold, disable the heater side.
								if float(fanTemp) > float(fanProbe.target_temperature) and float(wortTemp) > float(targetTemp):
									ssr_controller.setEnabled(True);
									ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
								else:
									ssr_controller.setEnabled(False);
									

	#
	# starts fermpi and starts reading temperatures and will set the heaters on/off based on current/target temps
	#
	def run(self):
		#lastJson = self.getLocalJson()
		
		while not self.stopped():
			self.updateTemps()
			self.checkBrew()
			self.checkFerm()
			Status.create().save()
			time.sleep(1)
			
                
#Pyro4.config.HMAC_KEY='derp'
def main():
	raspbrew=Raspbrew()
	raspbrew.run()
	
if __name__=="__main__":
	try:
		main()
	except KeyboardInterrupt:
		print "KeyboardInterrupt"
