from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
import time, datetime
import json, base64
from django.utils import timezone
from datetime import datetime, timedelta
import numpy as np

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
	one_wire_Id = models.CharField(null=True, blank=True, max_length=30, unique=True)
	name = models.CharField(max_length=30)
	type = models.IntegerField(default=0, choices=PROBE_TYPE)
	temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current temperature. Returns c or f depending on the global units
	target_temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current target temperature. Returns c or f depending on the global units
	correction_factor = models.DecimalField(default=0.0, decimal_places=3, max_digits=6) #a correction factor to apply (if any)
	
	#returns a tuple of the ETA epoch of the current target temp
	# as well as the degrees per minute
	def getETA(self):
		eta=None
		degreesPerMinute=None
		
		if self.target_temperature:
			#get the temps for this probe for the last 60 minutes
			now = timezone.now()
			startDate = now + timedelta(hours=-1)
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
						t=j['probes'][str(self.id)]
					
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
					print "%f %f %f" % (float(tempDiffThisHour), float(startTemp), float(currentTemp));
					degreesPerMinute=tempDiffThisHour/60

				if currentTemp and self.target_temperature:
					diff=float(self.target_temperature)-currentTemp
					print "diff: " + str(diff) + " degreesPerMinute:" + str(degreesPerMinute)
					eta=abs(diff/degreesPerMinute)
					print "minutes: " + str(eta)
					eta = now + timedelta(minutes=eta)
					eta = time.mktime(eta.timetuple())

				# test for y = mx + c
# 				x = np.array(_x)
# 				y = np.array(_y)
# 			
# 				A = np.vstack([x, np.ones(len(x))]).T
# 				m, c = np.linalg.lstsq(A, y)[0]
# 			
# 				# test for x = y/m - c
# 				eta = float(self.target_temperature)/m - c
				print str(eta)
			
		return eta, degreesPerMinute
			
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
	probe = models.ForeignKey(Probe, null=True)
	pid = models.OneToOneField(PID, null=True)
	
	#an ssr is a heater or a chiller
	HEATER_OR_CHILLER = (
		(0, 'Heater'),
		(1, 'Chiller'),
	)
	name = models.CharField(max_length=30)
	pin = models.IntegerField()
	heater_or_chiller = models.IntegerField(default=0, choices=HEATER_OR_CHILLER)
	
	enabled = models.BooleanField(default=True) #enabled
	state = models.BooleanField(default=False) #on/off
	
	def __unicode__(self):
		return self.name
	
	def save(self):
		# create a PID
		if not self.pid:
			self.pid = PID.objects.create()
        	
		super(SSR, self).save()
        
	class Meta:
		verbose_name = "SSR"
		verbose_name_plural = "SSRs"

# This should be a singleton that contains global configuration	
# class GlobalConfiguration(models.Model):
# 	UNITS = (
# 		(0, 'Metric'),
# 		(1, 'Imperial'),
# 	)
# 
# 	units = models.IntegerField(default=0, choices=UNITS)
# 	
# 	def __unicode__(self):
# 		return "Global Configuration"
# 		
# 	class Meta:
# 		verbose_name = "Global Configuration"
# 		verbose_name_plural = "Global Configuration"
		
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
					
#this class stores the current status as a json string in the db
class Status(models.Model):
	
	@classmethod
	def create(cls):
		
		jsonOut = {'probes': {}, 'ssrs': {}, 'date' : time.time()}
		
		probes=Probe.objects.all()
		for probe in probes:
			jsonOut['probes'][probe.pk] = {}
			jsonOut['probes'][probe.pk]['name'] = probe.name
			jsonOut['probes'][probe.pk]['id'] = probe.one_wire_Id
			if probe.getCurrentTemp() > -999:
				jsonOut['probes'][probe.pk]['temp'] = probe.getCurrentTemp()
			jsonOut['probes'][probe.pk]['target_temp'] = probe.target_temperature
			eta, degreesPerMinute = probe.getETA()
			if eta:
				jsonOut['probes'][probe.pk]['eta'] = eta
			if degreesPerMinute:
				jsonOut['probes'][probe.pk]['dpm'] = degreesPerMinute
			
		
		ssrs=SSR.objects.all()
		for ssr in ssrs:
			jsonOut['ssrs'][ssr.pk] = {}
			jsonOut['ssrs'][ssr.pk]['pid'] = {}
			jsonOut['ssrs'][ssr.pk]['pid']['cycle_time'] = ssr.pid.cycle_time
			jsonOut['ssrs'][ssr.pk]['pid']['k_param'] = ssr.pid.k_param
			jsonOut['ssrs'][ssr.pk]['pid']['i_param'] = ssr.pid.i_param
			jsonOut['ssrs'][ssr.pk]['pid']['d_param'] = ssr.pid.d_param
			
			jsonOut['ssrs'][ssr.pk]['name'] = ssr.name
			jsonOut['ssrs'][ssr.pk]['pin'] = ssr.pin
			jsonOut['ssrs'][ssr.pk]['state'] = ssr.state
			jsonOut['ssrs'][ssr.pk]['enabled'] = ssr.enabled
			
		units=GlobalSettings.objects.get_setting('UNITS')
		jsonOut['config'] = {'units' : units.value}
		
		jsonOut = json.dumps(jsonOut, cls=DjangoJSONEncoder)
		
		#print jsonOut	
		#print status
		_status = base64.encodestring(jsonOut)
		try:
			status = Status.objects.get(status=_status)
			print "already exists"
		except Status.DoesNotExist:
			status = Status(status=_status)
		
		status.date = timezone.now()
		
		#print base64.decodestring(status.status)
		return status
			
	#TODO - get as an object i guess? or just use the probe objects directly
			
	date = models.DateTimeField()
	status = models.CharField(max_length=10000)