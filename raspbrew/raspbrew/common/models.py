from django.db import models
import time
import json

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
	
	def getCurrentTemp(self):
		try:
			f = open('/sys/bus/w1/devices/' + self.one_wire_Id + "/w1_slave", 'r')
		except IOError as e:
			print "Error: File " + self.tempDir + self.fileName + "/w1_slave" + " does not exist.";	
			return -999; 

		lines=f.readlines()
		crcLine=lines[0]
		tempLine=lines[1]
		result_list = tempLine.split("=")
			
		temp = float(result_list[-1])/1000 # temp in Celcius

		if self.correction_factor != None:
			temp = temp + self.correction_factor # correction factor
		
		self.temperature = temp
				
		#temp = (9.0/5.0)*temp + 32  #convert to F
		if crcLine.find("NO") > -1:
			temp = -999
				
		return temp
	
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
	probe = models.OneToOneField(Probe, null=True)
	pid = models.OneToOneField(PID, null=True)
	
	HEATER_OR_CHILLER = (
		(0, 'Heater'),
		(1, 'Chiller'),
	)
	name = models.CharField(max_length=30)
	pin = models.IntegerField()
	heater_or_chiller = models.IntegerField(default=0, choices=HEATER_OR_CHILLER)

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
class GlobalConfiguration(models.Model):
	UNITS = (
		(0, 'Metric'),
		(1, 'Imperial'),
	)
	FERMENTATION_MODE = (
		(0, 'Regular'),
		(1, 'Coolbot'),
	)
	
	units = models.IntegerField(default=0, choices=UNITS)
	mode = models.IntegerField(default=0, choices=FERMENTATION_MODE)
	
	def __unicode__(self):
		return "Global Configuration"
		
	class Meta:
		verbose_name = "Global Configuration"
		verbose_name_plural = "Global Configuration"
		
#this class stores the current status as a json string in the db
class CurrentStatus(models.Model):
	
	@classmethod
	def create(cls):
		status = cls()
        
		jsonOut = {'probes': {}, 'ssrs': {}, 'date' : time.time()}
		
		probes=Probe.objects.all()
		for probe in probes:
			jsonOut['probes'][probe.name] = {}
			jsonOut['probes'][probe.name]['id'] = probe.one_wire_Id
			jsonOut['probes'][probe.name]['temp'] = probe.getCurrentTemp()
			jsonOut['probes'][probe.name]['target_temp'] = probe.target_temperature
		
		ssrs=SSR.objects.all()
		for ssr in ssrs:
			jsonOut['ssrs'][ssr.name] = {}
			jsonOut['ssrs'][ssr.name]['pid'] = {}
			jsonOut['ssrs'][ssr.name]['pid']['cycle_time'] = ssr.pid.cycle_time
			jsonOut['ssrs'][ssr.name]['pid']['k_param'] = ssr.pid.k_param
			jsonOut['ssrs'][ssr.name]['pid']['i_param'] = ssr.pid.i_param
			jsonOut['ssrs'][ssr.name]['pid']['d_param'] = ssr.pid.d_param
			
			jsonOut['ssrs'][ssr.name]['pin'] = ssr.pin
		
		conf=GlobalConfiguration.objects.all()
		if conf:
			print conf[:1].get();
		
		jsonOut = json.dumps(jsonOut)
		
		print jsonOut	
		print status
		
		return status
		#super(SSR, self).save()
	
	#TODO - get as an object i guess? or just use the probe objects directly
			
	date = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=10000)