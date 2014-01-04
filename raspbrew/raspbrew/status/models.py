from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe, SSR, PID, GlobalSettings
from copy import deepcopy
from django.core.serializers.json import DjangoJSONEncoder 
import os, time, json, datetime, time
from django.utils import timezone

#this class stores the current status
class ProbeStatus(models.Model):
	one_wire_Id = models.CharField(null=True, blank=True, max_length=30)
	name = models.CharField(max_length=30)
	type = models.IntegerField(default=0)
	temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current temperature. Returns c or f depending on the global units
	target_temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  #the probe's current target temperature. Returns c or f depending on the global units
	correction_factor = models.DecimalField(default=0.0, decimal_places=3, max_digits=6) #a correction factor to apply (if any)
	
	#the original Probe
	probe = models.ForeignKey('common.Probe', null=True)
	
	@classmethod
	def cloneFrom(cls, probe):
		p=cls()
		p.probe = probe
		p.one_wire_Id = probe.one_wire_Id
		p.name = probe.name
		p.type = probe.type
		p.temperature = probe.temperature
		p.target_temperature = probe.target_temperature
		p.correction_factor = probe.correction_factor

		p.save()
		
		for ssr in probe.ssr_set.all():
			#update the ssrs
			newssr = SSRStatus.cloneFrom(ssr)
			p.ssrstatus_set.add(newssr)
		
		p.save()
		return p

class PIDStatus(models.Model):
	cycle_time = models.FloatField(default=2.0)
	k_param = models.FloatField(default=70.0)
	i_param = models.FloatField(default=80.0)
	d_param = models.FloatField(default=4.0)
	
	#the original pid
	pid = models.ForeignKey('common.PID', null=True)
	
	@classmethod
	def cloneFrom(cls,_pid):
		pid = cls()
		pid.pid = _pid
		pid.cycle_time = _pid.cycle_time
		pid.k_param = _pid.k_param
		pid.i_param = _pid.i_param
		pid.d_param = _pid.d_param
		
		pid.save()
		return pid
		
class SSRStatus(models.Model):
	#an ssr is directly tied to a probe and a pid
	name = models.CharField(max_length=30)
	pin = models.IntegerField()
	enabled = models.BooleanField(default=True) #enabled
	state = models.BooleanField(default=False) #on/off
	heater_or_chiller = models.IntegerField(default=0)
	
	probe = models.ForeignKey(ProbeStatus, null=True)
	pid = models.OneToOneField(PIDStatus, null=True)
	
	#the original ssr
	ssr = models.ForeignKey('common.SSR', null=True)
	
	@classmethod
	def cloneFrom(cls,_ssr):
		ssr = cls()#deepcopy(_ssr)
		ssr.ssr = _ssr
		ssr.name = _ssr.name
		ssr.pin = _ssr.pin
		ssr.enabled = _ssr.enabled
		ssr.state = _ssr.state
		ssr.heater_or_chiller = _ssr.heater_or_chiller
		
		if _ssr.pid:
			ssr.pid = PIDStatus.cloneFrom(_ssr.pid)
		ssr.save()
		
		return ssr

				
class Status(models.Model):
	
	#status can be for a FermConfiguration
	fermconfig = models.ForeignKey('ferm.FermConfiguration',null=True, blank=True)
	#or a BrewConfiguration
	brewconfig = models.ForeignKey('brew.BrewConfiguration',null=True, blank=True)
	
	#and contains copies of probes
	probes = models.ManyToManyField(ProbeStatus,null=True, blank=True)
	
	date = models.DateTimeField(default=timezone.now()) #time of this status
	
	status = models.CharField(max_length=10000, default="")
	
	#override save
	def save(self, *args, **kwargs):
		# save this as json
		#if self.probes.all():
		
		#have to save this here so we can use the m2m associations
		super(Status, self).save(*args, **kwargs)
		
		status = self.toJson(True)
		if (len(status) < 10000):
			self.status = status
			super(Status, self).save(*args, **kwargs)
			
		
	#returns json for this status
	def getJsonObject(self):
		fermpk=None
		brewpk=None
		if self.fermconfig:
			fermpk = self.fermconfig.pk
		if self.brewconfig:
			brewpk = self.brewconfig.pk
		jsonOut = {'probes': {}, 'ssrs': {}, 'fermconf': fermpk, 'brewconf': brewpk, 'date' : time.mktime(self.date.timetuple())}
		
		probes=self.probes.all() #Probe.objects.all()
		for probe in probes:
			id=probe.probe.pk
			jsonOut['probes'][id] = {}
			jsonOut['probes'][id]['name'] = probe.name
			jsonOut['probes'][id]['id'] = probe.one_wire_Id
			if probe.temperature > -999:
				jsonOut['probes'][id]['temp'] = probe.temperature
			jsonOut['probes'][id]['target_temp'] = probe.target_temperature
			
			#ssrs=SSR.objects.all()
			#for ssr in ssrs:
			for ssr in probe.ssrstatus_set.all():
				ssrid=ssr.ssr.pk
				jsonOut['ssrs'][ssrid] = {}
				jsonOut['ssrs'][ssrid]['pid'] = {}
				jsonOut['ssrs'][ssrid]['pid']['cycle_time'] = ssr.pid.cycle_time
				jsonOut['ssrs'][ssrid]['pid']['k_param'] = ssr.pid.k_param
				jsonOut['ssrs'][ssrid]['pid']['i_param'] = ssr.pid.i_param
				jsonOut['ssrs'][ssrid]['pid']['d_param'] = ssr.pid.d_param
			
				jsonOut['ssrs'][ssrid]['name'] = ssr.name
				jsonOut['ssrs'][ssrid]['pin'] = ssr.pin
				jsonOut['ssrs'][ssrid]['state'] = ssr.state
				jsonOut['ssrs'][ssrid]['enabled'] = ssr.enabled
			
				#add the eta if we're heating or chilling
				probe = ssr.probe
				currentTemp = probe.temperature #getCurrentTemp()
			
				#TODO - this is for regular mode.. add coolbot mode and brewing mode
				if ssr.enabled and probe.target_temperature and currentTemp:
					eta, degreesPerMinute = ssr.ssr.getETA()
					#print "--------"
					#print str(ssr.enabled) + " " + str(ssr.heater_or_chiller) + " " + str(probe.target_temperature) + " " + str(currentTemp)
					if (ssr.heater_or_chiller == 0 and probe.target_temperature > currentTemp) or (ssr.heater_or_chiller == 1 and probe.target_temperature < currentTemp):
						if eta:
							jsonOut['ssrs'][ssrid]['eta'] = eta
						if degreesPerMinute:
							jsonOut['ssrs'][ssrid]['dpm'] = degreesPerMinute
		
		units=GlobalSettings.objects.get_setting('UNITS')
		jsonOut['config'] = {'units' : units.value}
		
		return jsonOut
	
	def toJson(self, forceUpdate=False):
	
		if self.status and not forceUpdate:
			return self.status
		else:
			jsonOut=self.getJsonObject()
			
		jsonOut = json.dumps(jsonOut, cls=DjangoJSONEncoder)
		#print jsonOut	
		#print status
		#_status = base64.encodestring(jsonOut)
		#try:
		#	status = Status.objects.get(status=_status)
		#	print "already exists"
		#except Status.DoesNotExist:
		#	status = Status(status=_status)
		
		# status.date = timezone.now()
		
		#print base64.decodestring(status.status)
		return jsonOut

	