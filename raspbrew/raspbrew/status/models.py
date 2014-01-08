from django.db import models
from raspbrew import settings
#from raspbrew.common.models import Probe, SSR, PID
from raspbrew.globalsettings.models import GlobalSettings
from copy import deepcopy
from django.core.serializers.json import DjangoJSONEncoder 
import os, time, json, time
from datetime import datetime
from django.utils import timezone

def unix_time(dt):
	dt=dt.replace(tzinfo=None)
	epoch = datetime.fromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()

def unix_time_millis(dt):
	return unix_time(dt) * 1000.0
	
#this class stores the current status
class ProbeStatus(models.Model):
	one_wire_Id = models.CharField(null=True, blank=True, max_length=30)
	name = models.CharField(max_length=30)
	type = models.IntegerField(default=0)
	
	#the probe's current temperature. Returns c or f depending on the global units
	temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  
	
	#the probe's current target temperature. Returns c or f depending on the global units
	target_temperature = models.DecimalField(null=True, blank=True, decimal_places=3, max_digits=6)  
	
	#a correction factor to apply (if any)
	correction_factor = models.DecimalField(default=0.0, decimal_places=3, max_digits=6) 
	
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
	power = models.IntegerField(default=100)
	enabled = models.BooleanField(default=True) #enabled
	
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
		pid.power = _pid.power
		pid.enabled = _pid.enabled
		
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
	
	status = models.CharField(max_length=10000,null=True, blank=True)
	
	#override save
	def save(self, *args, **kwargs):
		
		if self.pk:
			#have to save this here so we can use the m2m associations
			#super(Status, self).save(*args, **kwargs)
			if not self.status or self.status == "":
				#print str(self.pk) + " saving status, forcing update"
				status = self.toJson(forceUpdate=True)
				if (status and len(status) < 10000):
					self.status = status
		
		super(Status, self).save(*args, **kwargs)
			
		
	#returns json for this status
	def getJsonObject(self, addEta=False):
		
		fermpk=None
		brewpk=None
		if self.fermconfig:
			fermpk = self.fermconfig.pk
		if self.brewconfig:
			brewpk = self.brewconfig.pk
			
		jsonOut = {'pk' : self.pk, 'probes': {}, 'ssrs': {}, 'fermconf': fermpk, 'brewconf': brewpk, 'date' : unix_time_millis(self.date)}
		
		probes=self.probes.all() #Probe.objects.all()
		
		if not probes:
			return None
			
		for probe in probes:
				
			id=probe.probe.pk
			jsonOut['probes'][id] = {}
			jsonOut['probes'][id]['name'] = probe.name
			jsonOut['probes'][id]['id'] = probe.one_wire_Id
			
			currentTemp = probe.temperature
			if currentTemp > -999:
				jsonOut['probes'][id]['temp'] = currentTemp
			
			jsonOut['probes'][id]['target_temp'] = probe.target_temperature
			jsonOut['probes'][id]['ssrs'] = [];
			
			#ssrs=SSR.objects.all()
			#for ssr in ssrs:
			for ssr in probe.ssrstatus_set.all():
				ssrid=ssr.ssr.pk
				jsonOut['probes'][id]['ssrs'].append(ssrid)
				
				jsonOut['ssrs'][ssrid] = {}
				jsonOut['ssrs'][ssrid]['pid'] = {}
				
				jsonOut['ssrs'][ssrid]['pid']['cycle_time'] = ssr.pid.cycle_time
				jsonOut['ssrs'][ssrid]['pid']['k_param'] = ssr.pid.k_param
				jsonOut['ssrs'][ssrid]['pid']['i_param'] = ssr.pid.i_param
				jsonOut['ssrs'][ssrid]['pid']['d_param'] = ssr.pid.d_param
				jsonOut['ssrs'][ssrid]['pid']['power'] = ssr.pid.power
			
				jsonOut['ssrs'][ssrid]['name'] = ssr.name
				jsonOut['ssrs'][ssrid]['pin'] = ssr.pin
				jsonOut['ssrs'][ssrid]['heater_or_chiller'] = ssr.heater_or_chiller
				
				#update the state and enabled from the actual ssr
				jsonOut['ssrs'][ssrid]['state'] = ssr.ssr.state
				jsonOut['ssrs'][ssrid]['enabled'] = ssr.ssr.enabled

				#if this is a brew config, we have a current_ssr setting
				# if self.brewconfig:
				# 	if ssr.ssr.current_ssr:
				# 		jsonOut['ssrs'][ssrid]['current_ssr'] = True
				# 	else:
				# 		jsonOut['ssrs'][ssrid]['current_ssr'] = False

				#add the eta if we're heating or chilling
				if addEta:
					probe = ssr.ssr.probe
					currentTemp = probe.temperature
					
					#TODO - this is for regular mode.. add coolbot mode and brewing mode
					if probe.target_temperature and currentTemp:
						eta, degreesPerMinute = ssr.ssr.getETA()
						if eta and degreesPerMinute:
							jsonOut['ssrs'][ssrid]['eta'] = eta
							jsonOut['ssrs'][ssrid]['dpm'] = degreesPerMinute
								
		units=GlobalSettings.objects.get_setting('UNITS')
		jsonOut['config'] = {'units' : units.value}
		
		return jsonOut
	
	def toJson(self, forceUpdate=False, addEta=False):
		#print str(self.pk) + " " + str(forceUpdate)  + " " + str(addEta)
		#print self.status
		if self.status and not forceUpdate and not addEta:
			#print "Just returning status"
			return self.status
		else:
			#print "updating status!"
			jsonOut=self.getJsonObject(addEta=addEta)
			jsonOut = json.dumps(jsonOut, cls=DjangoJSONEncoder)
			self.status = jsonOut
			self.save()
		
		return jsonOut

	
