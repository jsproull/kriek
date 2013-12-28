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

from raspbrew.common.models import Probe,CurrentStatus,SSR
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
		#an array of ssr controllers
		self.ssrs = []
		self.pids = []
		
		self.power_cycle_time = 5.0 #used when setting 80% power - move to ferm/brew configs
		
		probes=Probe.objects.all()
		self.probes = probes
		
		# we have to go through all the FermConfiguration and BrewConfigurations
		
		ssrs=SSR.objects.all()
		for ssr in ssrs:
			s=ssrController(ssr)
			s.start()
			self.ssrs.append(s)
			
			if ssr.pid:
				pid=PIDController.pidpy(ssr.pid)
				self.pids.append(pid)
    	
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
			return probes[0]
		else:
			return None
			

	#returns the fermentation fan probe (if any) from the provided fermentation configuration	
	def getFanProbe(self, fermConf):
		return self.getProbeByType(ferConf,5)

	#returns the fermentation wort probe (if any) from the provided fermentation configuration	
	def getWortProbe(self, fermConf):
		return self.getProbeByType(ferConf,3)
			
	

	#
	# called from the main thread to fire the brewing ssrs (if configured)
	#
	def checkBrew(self):
		pass
	
	#
	# called from the main thread to fire the brewing ferm (if configured)
	#	
	def checkFerm(self):
		#do we have any fermentation probes?
		fermConfs = FermConfiguration.objects.all();
		
		for fermConf in fermConfs:
			wortProbe=self.getWortProbe
			
			if not wortProbe:
				print "Error: You need at least one Wort probe to run in any fermentation mode."
				
			wortTemp=wortProbe.getCurrentTemperature()
			if fermConf.mode == 0: # regular mode
			
				for ssr in fermConf.ssrs.all():
					ssr_controller=ssrController(ssr)
					#ssr = ssrController.ssr
					probe = ssr.probe
					pid = ssr. pid
			
					currentTemp = probe.getCurrentTemp()
					targetTemp = probe.target_temperature
					print "Current Temps: " + str(currentTemp) + " " + str(targetTemp)
					if currentTemp > -999 and targetTemp != None:
						if fermConf.mode == 0: # regular mode
				
							print "Regular: " + str(currentTemp) + " " + str(targetTemp) + " Heater? " + str(ssr.heater_or_chiller == 0)
							if float(currentTemp) < float(targetTemp):
								ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
								ssr_controller.setEnabled(ssr.heater_or_chiller == 0) #Heater
							elif float(currentTemp) > float(targetTemp):
								ssr_controller.updateSSR(ssr_controller.getPower(), self.power_cycle_time)
								ssr_controller.setEnabled(ssr.heater_or_chiller == 1) #chiller
							else:
								ssr_controller.setEnabled(False);
						
			elif fermConf.mode == 1: # coolbot
				fanProbe=self.getFanProbe(fermConf)
				if not fanProbe:
					print "Error: You need at least one AC Fan probe to run in 'coolbot' mode"
						
				fanTemp=fanProbe.getCurrentTemp()
				print fanProbe
						#coolbot mode
						#ensre we have a fan and a wort temp probe
						#if self.currentWortTe# mp > -999:
# 							lastWortTemp=self.currentWortTemp
# 							#if the wort is too high, turn on the heater which heats up the AC's thermoprobe so the compressor goes on
# 							if float(self.currentWortTemp) > float(self.targetWortTemp):
# 									self.fermHeater.setEnabled(True);
# 									self.fermHeater.updateHeater(self.fermHeater.getPower(), self.power_cycle_time)
# 							elif float(self.currentWortTemp) < float(self.targetWortTemp):
# 									self.fermHeater.setEnabled(False);
# 
# 						if self.currentFanTemp > -999:
# 							#if the fan coils aren't too cold, enable the AC unit
# 							if float(self.currentFanTemp) > float(self.targetFanTemp) and float(lastWortTemp) > float(self.targetWortTemp):
# 									self.fermChiller.setEnabled(True);
# 									self.fermChiller.updateHeater(self.fermChiller.getPower(), self.power_cycle_time)
# 							else:
# 									self.fermChiller.setEnabled(False);
						print "Coolbot: " + str(currentTemp) + " " + str(targetTemp)
		

	#
	# starts fermpi and starts reading temperatures and will set the heaters on/off based on current/target temps
	#
	def run(self):
		#lastJson = self.getLocalJson()
		
		while not self.stopped():
			self.checkBrew()
			self.checkFerm()
			time.sleep (5)
			
                
#Pyro4.config.HMAC_KEY='derp'
def main():
	raspbrew=Raspbrew()
	raspbrew.run()
	
if __name__=="__main__":
	try:
		main()
	except KeyboardInterrupt:
		print "innerupts"
		#kill daemon somehow?
		pass
