#!../../env-raspbrew/bin/python
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
##  This version stores everything locally
##
##  December 26, 2013 - V3.0 for Raspberry Pi
##


import sys
import os
import glob

sys.path.insert(0, "../")
sys.path.insert(0, "/home/pi/t/raspbrew/raspbrew/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from django.utils import timezone
from django.contrib.auth.models import User

from datetime import timedelta

from common.ssr import SSRController as ssrController
from datetime import datetime
import threading
import time

from raspbrew.common.models import Probe
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

class BaseThreaded(threading.Thread):
	"""

	"""

	def __init__(self, *args, **kwargs):
		threading.Thread.__init__(self, *args, **kwargs)

		self.daemon = True

		#create an event so we can stop
		self._stop = threading.Event()

		#a dictionary of ssr controllers
		self.ssrControllers = {}


	#returns an ssr controller for an ssr by its pk
	def getSSRController(self, ssr):
		try:
			s=self.ssrControllers[ssr.pk]
		except KeyError, e:
			self.ssrControllers[ssr.pk]=ssrController(ssr)
			s=self.ssrControllers[ssr.pk]
			s.start()

		return s

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


#We have 3
class Fermentation(BaseThreaded):
	"""
	A threaded class to check on the current Fermentation Configuration
	"""
	def __init__(self, *args, **kwargs):
		BaseThreaded.__init__(self, *args, **kwargs)

	def run(self):
		while not self.stopped():
			self.checkFerm()
			time.sleep(2)

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

			else:

				for wortProbe in wortProbes:
					wortTemp=wortProbe.getCurrentTemp()
					ssrs=wortProbe.ssrs.all()

					for ssr in ssrs:
						ssr_controller=self.getSSRController(ssr)

						#for now, all fermentation pids are disabled and we just use 100%
						ssr.pid.enabled=False

						probe = ssr.probe
						targetTemp = probe.target_temperature

						#if we have schedules assigned, use the current set time
						if fermConf.schedules:
							for schedule in fermConf.schedules.filter(probe=probe):
								_targetTemp = schedule.getTargetTemperature()
								if _targetTemp:
									targetTemp = _targetTemp

						if wortTemp == -999 or targetTemp is None:
							continue

						if ssr.enabled:
							#print "current " + str(wortTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
							if fermConf.mode == 0: # regular mode

								if float(wortTemp) < float(targetTemp):
									ssr_controller.setEnabled(ssr.heater_or_chiller == 0)
									ssr_controller.setState(ssr.heater_or_chiller == 0)
									#ssr_controller.updateSSRController(wortTemp, targetTemp, ssr.heater_or_chiller == 0)
								elif float(wortTemp) > float(targetTemp):
									ssr_controller.setEnabled(ssr.heater_or_chiller == 1)
									ssr_controller.setState(ssr.heater_or_chiller == 1)
									#ssr_controller.updateSSRController(wortTemp, targetTemp, ssr.heater_or_chiller == 1)
								else:
									ssr_controller.setEnabled(False)

							elif fermConf.mode == 1: # chiller

								fanProbes=self.getFanProbes(fermConf)
								if not fanProbes:
									print "Error: You need at least one AC Fan probe to run in 'coolbot' fermentation mode."
									continue

								for fanProbe in fanProbes:
									fanTemp=fanProbe.getCurrentTemp()

									if ssr.heater_or_chiller == 1: #chiller
										if float(wortTemp) > float(targetTemp):
											#ssr_controller.updateSSRController(wortTemp, targetTemp, True)
											ssr_controller.setEnabled(True);
											ssr_controller.setState(True)
										elif float(wortTemp) < float(targetTemp):
											ssr_controller.setEnabled(False);

									if float(fanTemp) > -999 and ssr.heater_or_chiller == 0: #heater
										#if the fan coils are too cold, disable the heater side.
										targetFanTemp = fanProbe.target_temperature
										if not targetFanTemp:
											targetFanTemp = -1

										if float(fanTemp) > float(targetFanTemp) and float(wortTemp) > float(targetTemp):
											ssr_controller.setEnabled(True);
											ssr_controller.setState(True)
											#ssr_controller.updateSSRController(wortTemp, targetTemp, True)
										else:
											ssr_controller.setEnabled(False);
						else:
							ssr_controller.setEnabled(False)

						if ssr.state != ssr_controller.isEnabled():
							ssr.state = ssr_controller.isEnabled()
							ssr.save()


class Brewing(BaseThreaded):
	"""
	A threaded class to check on the current Brewing Configuration(s)
	"""

	def __init__(self, *args, **kwargs):
		BaseThreaded.__init__(self, *args, **kwargs)

	def run(self):
		while not self.stopped():
			self.checkBrew()
			time.sleep(2)

	#
	# called from the main thread to fire the brewing ssrs (if configured)
	#
	def checkBrew(self):
		#do we have any fermentation probes?
		brewConfs = BrewConfiguration.objects.all()

		for brewConf in brewConfs:
			#safety check to ensure we don't have more than one ssr enabled
			if not brewConf.allow_multiple_ssrs:
				enabled=False
				for ssr in brewConf.ssrs.all():
					if enabled and ssr.enabled:
						ssr_controller = self.getSSRController(ssr)
						ssr.enabled = False
						ssr.save()
						ssr_controller.setEnabled(False)

					elif not enabled:
						enabled = ssr.enabled

			for ssr in brewConf.ssrs.all():
				currentTemp=ssr.probe.getCurrentTemp()

				targetTemp=ssr.probe.target_temperature

				#if we have schedules assigned, use those
				if brewConf.schedules:
					now=timezone.now()
					for schedule in brewConf.schedules.filter(probe=ssr.probe):
						_targetTemp = schedule.getTargetTemperature()
						if _targetTemp:
							targetTemp = _targetTemp

				ssr_controller=self.getSSRController(ssr)
				enabled = (targetTemp is not None and currentTemp > -999 and ssr.enabled)

				#print "ssr " + str(ssr) + " " + str(enabled) + " " + str(ssr.enabled)
					#or (brewConf.allow_multiple_ssrs == False and brewConf.current_ssr == ssr))
				if enabled:
					ssr_controller.updateSSRController(currentTemp, targetTemp, currentTemp < targetTemp)
				else:
					ssr_controller.setEnabled(False)

class Raspbrew(object):#threading.Thread):
	"""
	main class
	"""
	def __init__(self):
		self.user = User.objects.get(pk=1)
		self.ferm = Fermentation()
		self.brew = Brewing()

	# ensure all the temperatures are up to date
	def updateTemps(self):
		#print "updateTemps"
		probes = Probe.objects.all();
		for probe in probes:
			temp = probe.getCurrentTemp()
			print str(probe) + " " + str(temp) + " target:" + str(probe.target_temperature)

	#
	# Adds a Status object for all brewconf
	#
	def addBrewStatus(self):
		brewConfs = BrewConfiguration.objects.all()

		for brewConf in brewConfs:
			#print "Saving Status for brewConf: " + str(brewConf)
			status=Status(brewconfig=brewConf,date=timezone.now(),owner=self.user)
			status.save()
			for probe in brewConf.probes.all():
				status.probes.add(ProbeStatus.cloneFrom(probe))
			status.save()


	def addFermStatus(self):
		fermConfs = FermConfiguration.objects.all();

		for fermConf in fermConfs:
			#print "Saving Status for fermConf: " + str(fermConf)
			#add a status
			status=Status(fermconfig=fermConf, date=timezone.now(),owner=self.user)
			status.save()
			for probe in fermConf.probes.all():
				status.probes.add(ProbeStatus.cloneFrom(probe))
			status.save()

	#
	# we only keep data for every 15 minutes for fermenters if it's older than 1 day
	#
	def removeOldStatuses(self):
		fermConfs = FermConfiguration.objects.all()
		now=timezone.now()
		yesterday=now - timedelta(hours=24)
		minutes=15
		for fermConf in fermConfs:
			statuses = Status.objects.filter(date__lte=yesterday,fermconfig=fermConf).order_by('date')
			_len=len(statuses)
			if _len > 0:
				startDate=statuses[0].date
				dt=(now-startDate)
				totalMinutes=dt.days*24*60 + dt.seconds/60
				max = totalMinutes/minutes
				i=0
				if _len > max:
					while _len > 0 and startDate < yesterday:
						startDate=statuses[i].date
						todel=Status.objects.filter(date__gt=startDate, date__lte=startDate + timedelta(minutes=minutes),fermconfig=fermConf)
						c=todel.count()
						todel.delete()
						statuses=statuses[1+c:]
						_len=len(statuses)

	def update_probes(self):
		"""
		creates Probe ojbects for probes in /sys/bus/w1/devices/ if none currently exist in the db
		"""
		if Probe.objects.count() == 0:
			for dir in glob.glob("/sys/bus/w1/devices/28*"):
				file = os.path.basename(dir)
				print "Adding probe with one-wire id: " + str(file)
				user=User.objects.get(pk=1)
				probe=Probe(one_wire_Id=file,name=file,owner=user)
				probe.save()


	#
	# starts fermpi and starts reading temperatures and will set the heaters on/off based on current/target temps
	#
	def run(self):
		self.update_probes()
		self.ferm.start()
		self.brew.start()

		while True: #not self.stopped():
			self.updateTemps()
			self.addBrewStatus()
			self.addFermStatus()

			#remove old fermentation statuses
			self.removeOldStatuses()
			print "--- sleep ---"
			time.sleep(1)
			
                
#Pyro4.config.HMAC_KEY='derp'
def main(raspbrew):
	raspbrew.run()
	
if __name__=="__main__":
	try:
		raspbrew=Raspbrew()
		main(raspbrew)
	except KeyboardInterrupt:
		print "KeyboardInterrupt.. shutting down. Please wait."
		for pk in raspbrew.ferm.ssrControllers:
			try:
				raspbrew.ferm.ssrControllers[pk].stop()
			except AttributeError:
				pass
				
			time.sleep(2)

		for pk in raspbrew.brew.ssrControllers:
			try:
				raspbrew.brew.ssrControllers[pk].stop()
			except AttributeError:
				pass

			time.sleep(2)
