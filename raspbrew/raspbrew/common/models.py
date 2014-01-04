from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
import time, datetime
import json, base64
from django.utils import timezone
from datetime import datetime, timedelta

from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration

#import numpy as np

def unix_time(dt):
	dt=dt.replace(tzinfo=None)
	epoch = datetime.fromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()

def unix_time_millis(dt):
	return unix_time(dt) * 1000.0

# Each Probe.
class Probe(models.Model):
	PROBE_TYPE = (
		(0, 'Mash'),
		(1, 'Boil'),
		(2, 'Hot Liquor Tank'),
		(3, 'Fermentation Wort'),
		(4, 'Fermentation Room'),
		(5, 'Fermentation AC Fan'),
		(6, 'Other'),
	)
	one_wire_Id = models.CharField(null=True, blank=True, max_length=30)
	name = models.CharField(max_length=30)
	type = models.IntegerField(default=0, choices=PROBE_TYPE)
	temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current temperature. Returns c or f depending on the global units
	target_temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current target temperature. Returns c or f depending on the global units
	correction_factor = models.DecimalField(default=0.0, decimal_places=3, max_digits=6) #a correction factor to apply (if any)
	
	#returns the current temperature of this probe.
	def getCurrentTemp(self):
		units=GlobalSettings.objects.get_setting('UNITS')
		try:
			f = open('/sys/bus/w1/devices/' + self.one_wire_Id + "/w1_slave", 'r')
		except IOError as e:
			print "Error: File " '/sys/bus/w1/devices/' + self.one_wire_Id + "/w1_slave does not exist.";	
			return -999; 

		lines=f.readlines()
		crcLine=lines[0]
		tempLine=lines[1]
		result_list = tempLine.split("=")
			
		temp = float(result_list[-1])/1000 # temp in Celcius

		if self.correction_factor != None:
			temp = temp + float(self.correction_factor) # correction factor
				
		if crcLine.find("NO") > -1:
			temp = self.temperature
		
		if not temp:
			return -999
		
		#this is now all done on the client side
		#if units.value == 'imperial':
		#	temp = (9.0/5.0)*float(temp) + 32  #convert to F
		
		if (self.temperature != temp):
			self.temperature = temp
			probe = Probe.objects.get(pk=self.pk)
			probe.temperature = temp
			probe.save()
		
		return self.temperature
	
	def __unicode__(self):
		return self.name
        
	class Meta:
		verbose_name = "Probe"
		verbose_name_plural = "Probes"
        
# An internal PID class to contain PID values for each SSR
class PID(models.Model):
	cycle_time = models.FloatField(default=2.0)
	k_param = models.FloatField(default=70.0)
	i_param = models.FloatField(default=80.0)
	d_param = models.FloatField(default=4.0)

# An SSR has probe and PID information
class SSR(models.Model):
	#an ssr is directly tied to a probe and a pid
	name = models.CharField(max_length=30)
	pin = models.IntegerField()
	probe = models.ForeignKey(Probe, null=True)
	pid = models.OneToOneField(PID, null=True)
	enabled = models.BooleanField(default=True) #enabled
	state = models.BooleanField(default=False) #on/off
	
	#an ssr is a heater or a chiller
	HEATER_OR_CHILLER = (
		(0, 'Heater'),
		(1, 'Chiller'),
	)
	heater_or_chiller = models.IntegerField(default=0, choices=HEATER_OR_CHILLER)
	
	
	def __unicode__(self):
		return self.name
	
	def save(self, *args, **kwargs):
		# create a PID
		if not self.pid:
			self.pid = PID.objects.create()
        
		super(SSR, self).save(*args, **kwargs)
		
	class Meta:
		verbose_name = "SSR"
		verbose_name_plural = "SSRs"

	#returns a tuple of the ETA epoch of the current target temp
	# as well as the degrees per minute
	def getETA(self):
		eta=None
		degreesPerMinute=None
		
		if self.probe.target_temperature:
			#get the temps for this probe for the last 60 minutes
			now = timezone.now()
			startDate = now + timedelta(hours=-1)
			
			#todo - should just filter this by when the ssr state is true
			
			#start here tomorrow. ugh
			
			
			statuses = Status.objects.filter(date__gte=startDate, date__lte=now)
			if statuses and len(statuses) >= 2:
				
				_x=[]
				_y=[]
			
				currentTemp=None
				startTemp=None
				
				count=0
			
				for status in statuses:
					try:
						j=json.loads(base64.decodestring(status.status))
						t=j['probes'][str(self.probe.id)]
					
						if count==0:
							startTemp=float(t['temp'])
						elif count==len(statuses)-1:
							currentTemp=float(t['temp'])
							
						count=count+1
						
						_y.append(t['temp'])
						_x.append(unix_time_millis(status.date))
					except KeyError:
						pass
			
				if startTemp and currentTemp:
					tempDiffThisHour=currentTemp-startTemp
					degreesPerMinute=tempDiffThisHour/60
					#print "%d : target: %f tempdiff: %f start temp: %f current temp: %f dpm: %f" % (self.probe.pk , float(self.probe.target_temperature), float(tempDiffThisHour), float(startTemp), float(currentTemp), float(degreesPerMinute));


				if currentTemp and self.probe.target_temperature and degreesPerMinute and degreesPerMinute > 0:
					diff=float(self.probe.target_temperature)-currentTemp
					#print "diff: " + str(diff) + " degreesPerMinute:" + str(degreesPerMinute)
					eta=abs(diff/degreesPerMinute)
					#print "minutes: " + str(eta)
					#print "now: " + str(now)
					eta = now + timedelta(minutes=eta)
					#print "eta: " + str(eta)
					eta = time.mktime(eta.timetuple())
					#print "tuple: " + str(eta)

#				# test for y = mx + c
# 				x = np.array(_x)
# 				y = np.array(_y)
# 			
# 				A = np.vstack([x, np.ones(len(x))]).T
# 				m, c = np.linalg.lstsq(A, y)[0]
# 			
# 				# test for x = y/m - c
# 				eta = float(self.target_temperature)/m - c
			
		return eta, degreesPerMinute
			


# Global (application) settings

class GlobalSettingsManager(models.Manager):
	def get_setting(self, key):
		try:
			setting = GlobalSettings.objects.get(key=key)
		except:
			raise Exception
		return setting

class GlobalSettings(models.Model):
	key = models.CharField(unique=True, max_length=255)
	value = models.CharField(max_length=255)

	objects = GlobalSettingsManager()
      
	def __unicode__(self):
		return self.key + " : " + self.value
	
	class Meta:
		verbose_name = "Global Setting"
		verbose_name_plural = "Global Settings"