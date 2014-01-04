#!../env-raspbrew/bin/python
##                      _                       
##                     | |                      
##  _ __ __ _ ___ _ __ | |__  _ __ _____      __
## | '__/ _` / __| '_ \| '_ \| '__/ _ \ \ /\ / /
## | | | (_| \__ \ |_) | |_) | | |  __/\ V  V / 
## |_|  \__,_|___/ .__/|_.__/|_|  \___| \_/\_/  
##               | |                            
##               |_|                            
##
##  RaspBrew v3.0 
##
##  This class controls a fermentation chamber. It is responsible for reading 2 temp probes and logging both to sqlite.
##  It will also turn on a cooling/heating unit 
##
##  December 26, 2012 - V3.0 for Raspberry Pi
##

#sys.path.insert(0, "/home/pi/raspbrew")
import sys, os
from django.db.utils import OperationalError
from django.utils import timezone

from common.ssr import SSR as ssrController
import common.pidpy as PIDController
from datetime import datetime
import threading
import time
from django.db.utils import OperationalError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,SSR
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from raspbrew.status.models import ProbeStatus, Status

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
			 	s.start()
		
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
			temp = -999
			count=0
			while temp == -999 and count < 10:
				temp = probe.getCurrentTemp()
				count=count+1
				print str(probe) + " " + str(temp)
			
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
					#print "current " + str(currentTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
					ssr_controller.setEnabled(currentTemp < targetTemp)
					if ssr.pid.power < 100:
						if currentTemp < targetTemp:
							ssr_controller.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
					else:
						duty_cycle = pid_controller.calcPID_reg4(float(currentTemp), float(targetTemp), True)
						ssr_controller.updateSSR(duty_cycle, ssr.pid.cycle_time)
				else:
					ssr_controller.setEnabled(False)
			
			#add a status	
			status=Status(brewconfig=brewConf,date=timezone.now())
			status.save()
			for probe in brewConf.probes.all():
				status.probes.add(ProbeStatus.cloneFrom(probe))
				
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
				continue
			
					
			for wortProbe in wortProbes:	
				wortTemp=wortProbe.getCurrentTemp()
				ssrs=wortProbe.ssr_set.all()
				
				for ssr in ssrs:
					ssr_controller=self.getSSRController(ssr)
					probe = ssr.probe
					targetTemp = probe.target_temperature
					if wortTemp == -999 or targetTemp == None:
						continue
						
					if ssr.enabled:
						#print "current " + str(wortTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
						if fermConf.mode == 0: # regular mode
							if float(wortTemp) < float(targetTemp):
								ssr_controller.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
								ssr_controller.setEnabled(ssr.heater_or_chiller == 0) #Heater
							elif float(wortTemp) > float(targetTemp):
								ssr_controller.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
								ssr_controller.setEnabled(ssr.heater_or_chiller == 1) #chiller
							else:
								ssr_controller.setEnabled(False);
						
						elif fermConf.mode == 1: # chiller
				
							fanProbes=self.getFanProbes(fermConf)
							if not fanProbes:
								print "Error: You need at least one AC Fan probe to run in 'coolbot' fermentation mode."
								continue
								
							for fanProbe in fanProbes:	
								fanTemp=fanProbe.getCurrentTemp()
							
								if ssr.heater_or_chiller == 0: #heater
									if float(wortTemp) > float(targetTemp):
										ssr_controller.setEnabled(True) # enable all ssrs (heater and chiller side)
										ssr_controller.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
									elif float(wortTemp) < float(targetTemp):
										ssr_controller.setEnabled(False);
						
								if float(fanTemp) > -999 and ssr.heater_or_chiller == 0: #heater
									#if the fan coils are too cold, disable the heater side.
									if float(fanTemp) > float(fanProbe.target_temperature) and float(wortTemp) > float(targetTemp):
										ssr_controller.setEnabled(True);
										ssr_controller.updateSSR(ssr.pid.power, ssr.pid.cycle_time)
									else:
										ssr_controller.setEnabled(False);
					else:
						ssr_controller.setEnabled(False)
						
					if ssr.state != ssr_controller.isEnabled():
						ssr.state = ssr_controller.isEnabled()
						ssr.save()
				
				
			#add a status
			status=Status(fermconfig=fermConf, date=timezone.now())
			status.save()
			for probe in fermConf.probes.all():
				status.probes.add(ProbeStatus.cloneFrom(probe))
			status.save()
			
				
	#
	# starts fermpi and starts reading temperatures and will set the heaters on/off based on current/target temps
	#
	def run(self):
		while not self.stopped():
			print "--------"
			self.updateTemps()
			self.checkBrew()
			self.checkFerm()
			time.sleep(5)
			
                
#Pyro4.config.HMAC_KEY='derp'
def main(raspbrew):
	raspbrew.run()
	
if __name__=="__main__":
	try:
		raspbrew=Raspbrew()
		main(raspbrew)
	except KeyboardInterrupt:
		print "KeyboardInterrupt.. shutting down. Please wait."
		for pk in raspbrew.ssrControllers:
			try:
				raspbrew.ssrControllers[pk].stop()
			except AttributeError:
				pass
				
			time.sleep(2)
		
	except OperationalError:
		print "OperationalError"
		main()
