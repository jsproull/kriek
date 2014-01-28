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
##  It will also turn on a cooling/heating unit.
##
##  It will sync to xxxx.com
##
##  December 26, 2013 - V3.0 for Raspberry Pi
##

from raspbrew_local import Raspbrew
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from raspbrew.common.serializers import BrewConfSerializer, FermConfSerializer
from raspbrew.rest import Rest
from raspbrew.status.models import ProbeStatus, Status

from django.utils import timezone

from django.core import serializers
import time, json

class RaspbrewRemote(Raspbrew):#threading.Thread):
	"""
	RaspbrewRemote main class
	"""

	def __init__(self):
		"""


		"""
		self.rest = Rest()
		super(RaspbrewRemote, self).__init__()

	#
	# Adds a Status object for all brewconf
	#
	def addBrewStatus(self):
		brewConfs = BrewConfiguration.objects.all()

		for brewConf in brewConfs:
			print "Saving Status for brewConf: " + str(brewConf)
			status=Status(brewconfig=brewConf,date=timezone.now())
			status.save()
			for probe in brewConf.probes.all():
				status.probes.add(ProbeStatus.cloneFrom(probe))
			status.save()


	def addFermStatus(self):
		fermConfs = FermConfiguration.objects.all();

		for fermConf in fermConfs:
			print "Saving Status for fermConf: " + str(fermConf)
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
			_json=self.rest.sendRequest('ferms');
			_json=json.loads(_json)
			#print _json

			#print serializers.serialize('json', FermConfiguration.objects.all());

			try:
				if _json["count"] > 0:
					for fermConf in _json["results"]:
						#print "restoring"

						#FUCK IT -- just create the fucking things by hand

						#print fermConf

						fc,created=FermConfiguration.objects.get_or_create(name="TEST",owner=self.user)#pk=fermConf["id"],name=fermConf["name"])
						#print created
						fcnew=FermConfSerializer(fc)
						fcnew=FermConfSerializer(fc)
						fc=fcnew.restore_object(fermConf, fc)
						print "HI"
						print fc._nested_forward_relations
						print "saveing?"
						print fcnew
						fcnew.save_object(fc)
						print fcnew
			except Exception as e:
				print "exception"
				print e

			print "--------"
			# self.updateTemps()
			# self.checkBrew()
			# self.addBrewStatus()
			# self.checkFerm()
			# self.addFermStatus()
			print "--- sleep ---"
			time.sleep(10)
			
                
#Pyro4.config.HMAC_KEY='derp'
def main(raspbrew):
	raspbrew.run()
	
if __name__=="__main__":
	try:
		raspbrew=RaspbrewRemote()
		main(raspbrew)
	except KeyboardInterrupt:
		print "KeyboardInterrupt.. shutting down. Please wait."
		for pk in raspbrew.ssrControllers:
			try:
				raspbrew.ssrControllers[pk].stop()
			except AttributeError:
				pass
				
			time.sleep(2)
