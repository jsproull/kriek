#!../../env-kriek/bin/python
##
##  _         _      _
## | |       (_)    | |
## | | ___ __ _  ___| | __
## | |/ / '__| |/ _ \ |/ /
## |   <| |  | |  __/   <
## |_|\_\_|  |_|\___|_|\_\
##
##
##  kriek v1.0 alpha 1
##
##  This class controls a fermentation chamber. It is responsible for reading 2 temp probes and logging both to sqlite.
##  It will also turn on a cooling/heating unit
##
##  This version stores everything locally
##
##  Februrary 9, 2014 - v1.0 alpha 1 renamed to 'kriek'. initial alpha version.
##


import sys
import os
import glob

#sys.path.append('/opt/kriek/kriek')
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kriek.settings")

from django.utils import timezone
from django.contrib.auth.models import User

from datetime import timedelta

from common.ssr import SSRController as ssrController
import threading
import time

from kriek.common.models import Probe, SSR
from kriek.ferm.models import FermConfiguration
from kriek.brew.models import BrewConfiguration
from kriek.status.models import ProbeStatus, Status
from kriek.globalsettings.models import GlobalSettings


class BaseThreaded(threading.Thread):
	"""

	"""

	def __init__(self, *args, **kwargs):
		threading.Thread.__init__(self, *args, **kwargs)

		self.daemon = True

		#create an event so we can stop
		self._stop = threading.Event()

		#a dictionary of ssr controllers
		self.ssr_controllers = {}

	#returns an ssr controller for an ssr by its pk
	def get_ssr_controller(self, ssr):
		try:
			s = self.ssr_controllers[ssr.pk]
		except KeyError:
			self.ssr_controllers[ssr.pk] = ssrController(ssr)
			s = self.ssr_controllers[ssr.pk]
			s.start()

		return s

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	#returns true if the probe is a fermentation probe
	def is_ferm_ssr(self, ssr):
		return ssr.get_mode_display() == 'Fermentation Regular' or ssr.get_mode_display() == 'Fermentation Coolbot'

	#returns true if the probe is a brewing probe
	def is_brew_ssr(self, ssr):
		return not self.is_ferm_ssr(ssr)

	#returns the fermentation fan probe (if any) from the provided fermentation configuration
	def get_probe_by_type(self, ferm_conf, _type):
		probes = ferm_conf.probes.filter(type=_type)
		if probes:
			return probes
		else:
			return None

	#returns the fermentation fan probe (if any) from the provided fermentation configuration
	def get_fan_probes(self, ferm_conf):
		return self.get_probe_by_type(ferm_conf, 5)

	#returns the fermentation wort probe (if any) from the provided fermentation configuration
	def get_wort_probes(self, ferm_conf):
		return self.get_probe_by_type(ferm_conf, 3)


#We have 3
class Fermentation(BaseThreaded):
	"""
	A threaded class to check on the current Fermentation Configuration
	"""
	def __init__(self, *args, **kwargs):
		BaseThreaded.__init__(self, *args, **kwargs)

	def run(self):
		while not self.stopped():
			self.check_ferm()
			time.sleep(2)

	#
	# called from the main thread to fire the brewing ferm (if configured)
	#
	def check_ferm(self):
		#do we have any fermentation probes?
		ferm_confs = FermConfiguration.objects.all()

		for fermConf in ferm_confs:
			wort_probes = self.get_wort_probes(fermConf)

			if not wort_probes:
				print "Error: You need at least one Wort probe to run in any fermentation mode."

			else:

				for wortProbe in wort_probes:
					worttemp = wortProbe.get_current_temp()
					ssrs = wortProbe.ssrs.all()

					for ssr in ssrs:
						ssr_controller = self.get_ssr_controller(ssr)

						#for now, all fermentation pids are disabled and we just use 100%
						ssr.pid.enabled = False

						probe = ssr.probe
						target_temp = probe.target_temperature

						#if we have schedules assigned, use the current set time
						if fermConf.schedules:
							for schedule in fermConf.schedules.filter(probe=probe):
								_targetTemp = schedule.get_target_temperature()
								if _targetTemp:
									target_temp = _targetTemp

						if worttemp == -999 or target_temp is None:
							continue

						if ssr.enabled:
							#print "current " + str(wortTemp) + " : " + str(targetTemp) + " " + str(ssr.pid.power)
							if fermConf.mode == 0:  # regular mode

								if float(worttemp) < float(target_temp):
									ssr_controller.set_enabled(ssr.heater_or_chiller == 0)
									ssr_controller.set_state(ssr.heater_or_chiller == 0)
									#ssr_controller.updateSSRController(wortTemp, targetTemp, ssr.heater_or_chiller == 0)
								elif float(worttemp) > float(target_temp):
									ssr_controller.set_enabled(ssr.heater_or_chiller == 1)
									ssr_controller.set_state(ssr.heater_or_chiller == 1)
									#ssr_controller.updateSSRController(wortTemp, targetTemp, ssr.heater_or_chiller == 1)
								else:
									ssr_controller.set_enabled(False)

							elif fermConf.mode == 1:  # chiller

								fan_probes = self.get_fan_probes(fermConf)
								if not fan_probes:
									print "Error: You need at least one AC Fan probe to run in 'coolbot' fermentation mode."
									continue

								for fanProbe in fan_probes:
									fantemp = fanProbe.get_current_temp()

									if ssr.heater_or_chiller == 1:  # chiller
										if float(worttemp) > float(target_temp):
											#ssr_controller.updateSSRController(wortTemp, targetTemp, True)
											ssr_controller.set_enabled(True)
											ssr_controller.set_state(True)
										elif float(worttemp) < float(target_temp):
											ssr_controller.set_enabled(False)

									if float(fantemp) > -999 and ssr.heater_or_chiller == 0:  # heater
										#if the fan coils are too cold, disable the heater side.
										target_fan_temp = fanProbe.target_temperature
										if not target_fan_temp:
											target_fan_temp = -1

										if float(fantemp) > float(target_fan_temp) and float(worttemp) > float(target_temp):
											ssr_controller.set_enabled(True)
											ssr_controller.set_state(True)
											#ssr_controller.updateSSRController(wortTemp, targetTemp, True)
										else:
											ssr_controller.set_enabled(False)
						else:
							ssr_controller.set_enabled(False)

						if ssr.state != ssr_controller.is_enabled():
							ssr.state = ssr_controller.is_enabled()
							ssr.save()


class Brewing(BaseThreaded):
	"""
	A threaded class to check on the current Brewing Configuration(s)
	"""

	def __init__(self, *args, **kwargs):
		BaseThreaded.__init__(self, *args, **kwargs)

	def run(self):
		while not self.stopped():
			self.check_brew()
			time.sleep(2)

	#
	# called from the main thread to fire the brewing ssrs (if configured)
	#
	def check_brew(self):
		#do we have any fermentation probes?
		brew_confs = BrewConfiguration.objects.all()

		for brewConf in brew_confs:
			for probe in brewConf.probes.all():
				

				for ssr in probe.ssrs.all():
					currenttemp = ssr.probe.get_current_temp()

					targettemp = ssr.probe.target_temperature

					#if we have schedules assigned, use those
					if brewConf.schedules:
						for schedule in brewConf.schedules.filter(probe=ssr.probe):
							_targetTemp = schedule.get_target_temperature()
							if _targetTemp:
								targettemp = _targetTemp

					ssr_controller = self.get_ssr_controller(ssr)

					enabled = (targettemp is not None and currenttemp > -999 and ssr.enabled)

					#it's always enabled if it's in manual mode and was set 'enabled'
					if ssr.manual_mode:
						ssr_controller.update_ssr_controller(currenttemp, targettemp, True)
					else:
						#print "enabled: " + str(enabled) + " " + str(targettemp) + " " + str(currenttemp) + " " + str(ssr.enabled)

						if enabled:
							ssr_controller.update_ssr_controller(currenttemp, targettemp, currenttemp < targettemp)
						else:
							ssr_controller.set_enabled(False)

					if enabled:
						#safety check to ensure we don't have more than one ssr enabled
						if not brewConf.allow_multiple_ssrs:
							for _ssr in SSR.objects.all():
								if not ssr.id == _ssr.id:
									_ssr.enabled = False
									_ssr.save()


class Kriek(object):
	"""
	main class
	"""
	def __init__(self):
		self.user = User.objects.get(pk=1)
		self.ferm = Fermentation()
		self.brew = Brewing()

	# ensure all the temperatures are up to date
	def update_temps(self):
		#print "updateTemps"
		probes = Probe.objects.all()
		for probe in probes:
			temp = probe.get_current_temp()
			#print str(probe) + " " + str(temp) + " target:" + str(probe.target_temperature)

	#
	# Adds a Status object for all brewconf
	#
	def add_brew_status(self):
		brewconfs = BrewConfiguration.objects.all()

		for brewConf in brewconfs:
			#print "Saving Status for brewConf: " + str(brewConf)
			status = Status(brewconfig=brewConf, date=timezone.now(), owner=self.user)
			status.save()
			for probe in brewConf.probes.all():
				status.probes.add(ProbeStatus.clone_from(probe))
			status.save()

	def add_ferm_status(self):
		fermconfs = FermConfiguration.objects.all()

		for fermConf in fermconfs:
			#print "Saving Status for fermConf: " + str(fermConf)
			#add a status
			status = Status(fermconfig=fermConf, date=timezone.now(), owner=self.user)
			status.save()
			for probe in fermConf.probes.all():
				status.probes.add(ProbeStatus.clone_from(probe))
			status.save()

	#
	# we only keep data for every 15 minutes for fermenters if it's older than 1 day
	#
	def remove_old_statuses(self):
		fermconfs = FermConfiguration.objects.all()
		now = timezone.now()
		yesterday = now - timedelta(hours=24)
		minutes = 15
		for fermConf in fermconfs:
			statuses = Status.objects.filter(date__lte=yesterday, fermconfig=fermConf).order_by('date')
			_len = len(statuses)
			if _len > 0:
				startdate = statuses[0].date
				dt = (now-startdate)
				totalminutes = dt.days*24*60 + dt.seconds/60
				_max = totalminutes/minutes
				if _len > _max:
					while _len > 0 and startdate < yesterday:
						startdate = statuses[0].date
						todel = Status.objects.filter(date__gt=startdate, date__lte=startdate + timedelta(minutes=minutes), fermconfig=fermConf)
						c = todel.count()
						todel.delete()
						statuses = statuses[1+c:]
						_len = len(statuses)

	def update_probes(self):
		"""
		creates Probe ojbects for probes in /sys/bus/w1/devices/ if none currently exist in the db
		"""
		for _dir in glob.glob("/sys/bus/w1/devices/28*"):
			_file = os.path.basename(_dir)
			user = User.objects.get(pk=1)
			probe,created = Probe.objects.get_or_create(one_wire_id=_file, name=_file, owner=user)
			if created:
				print "Adding probe with one-wire id: " + str(_file)
				probe.save()

	#
	# starts fermpi and starts reading temperatures and will set the heaters on/off based on current/target temps
	#
	def run(self):
		self.update_probes()
		self.ferm.start()
		self.brew.start()

		while True:  # not self.stopped():
			self.update_temps()
			updates = GlobalSettings.objects.get_setting('UPDATES_ENABLED').value
			if (updates == True or updates == "True"):
				self.add_brew_status()
				self.add_ferm_status()

			#remove old fermentation statuses
			self.remove_old_statuses()
			#print "--- sleep ---"
			time.sleep(1)
			

def main(rb):
	rb.run()
	
if __name__ == "__main__":

	kriek = Kriek()

	try:
		main(kriek)
	except KeyboardInterrupt:
		print "KeyboardInterrupt.. shutting down. Please wait."
		for pk in kriek.ferm.ssr_controllers:
			try:
				kriek.ferm.ssr_controllers[pk].stop()
			except AttributeError:
				pass
				
			time.sleep(2)

		for pk in kriek.brew.ssr_controllers:
			try:
				kriek.brew.ssr_controllers[pk].stop()
			except AttributeError:
				pass

			time.sleep(2)
