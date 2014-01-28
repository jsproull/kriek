import time
from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from raspbrew.globalsettings.models import GlobalSettings
from raspbrew.status.models import Status, ProbeStatus

from django.db.models import Q

#import numpy as np

def unix_time(dt):
	dt = dt.replace(tzinfo=None)
	epoch = datetime.fromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()


def unix_time_millis(dt):
	return unix_time(dt) * 1000.0

##
## A ScheduleTime is one step by date in a Schedule
##
class ScheduleTime(models.Model):
	name = models.CharField(max_length=30)
	start_time = models.DateTimeField() #time of this status
	start_temperature = models.FloatField()
	end_temperature = models.FloatField(blank=True, null=True)
	end_time = models.DateTimeField() #end time of this status

	def getTargetTemperature(self):
		#if we just have a start time, return it
		if (self.start_temperature and not self.end_temperature) or self.start_temperature == self.end_temperature:
			return self.start_temperature

		#for now, assume it's linear
		diff = (self.end_time - self.start_time).total_seconds()
		now = timezone.now()
		curr = (now - self.start_time).total_seconds()
		percent = float(curr) / diff

		tempDiff = self.end_temperature - self.start_temperature
		temp = self.start_temperature + tempDiff * percent
		return round(temp, 1)


	#TODO
	#we have to add the ability to 'ramp up' over time
	#type = hold, linear, ease in, ease out

	def __unicode__(self):
		return "%s - %s" % (self.start_time, self.end_time)

##
## A ScheduleStep is one step that is held for x seconds in a Schedule
##
class ScheduleStep(models.Model):
	name = models.CharField(max_length=30)
	step_index = models.IntegerField()
	temperature = models.FloatField()
	active = models.BooleanField(default=False) # this is set to true when we are currently using this step (but not
	active_time = models.DateTimeField(null=True, blank=True) #and internal date to be set when this step starts
	hold_seconds = models.FloatField(default=60 * 15) #once the temperature is reached, it is held for this long

	def getTargetTemperature(self):
		return self.temperature

	def __unicode__(self):
		return "%d: %s" % (self.step_index, self.name)


##
## A Schedule can be used to set a temperature after a given time
##
class Schedule(models.Model):
	name = models.CharField(max_length=30)
	owner = models.ForeignKey('auth.User', related_name='schedules', blank=True, null=True)
	scheduleTime = models.ManyToManyField('common.ScheduleTime', blank=True, null=True)
	scheduleStep = models.ManyToManyField('common.ScheduleStep', blank=True, null=True)

	probe = models.ForeignKey('common.Probe', null=True, related_name='schedules')

	def getTargetTemperature(self):
		now = timezone.now()

		#check if we have any scheduleTimes
		q = Q(start_time__lte=now) & Q(end_time__gte=now)
		for _time in self.scheduleTime.filter(q):
			targetTemp = _time.getTargetTemperature()
			if targetTemp != self.probe.target_temperature:
				self.probe.target_temperature = targetTemp
				self.probe.save()

		#or any ScheduleSteps that are active
		for _step in self.scheduleStep.filter(active=True).order_by("step_index"):
			print "STEP"
			print _step
			now = timezone.now()
			print "active time: " + str(_step.active_time)
			if not _step.active_time:
				heating=False
				ssrs=self.probe.ssrs.all()
				#are we heating or cooling? TODO - figure out if this is coolbot mode
				for ssr in ssrs:
					heating=(ssr.heater_or_chiller == 0) # heater
					break #for now, just use the first one

				#check if we should start
				if heating:
					print "heating"
					print "self.probe.temperature >= _step.temperature"
					print str(self.probe.temperature) + " " + str(_step.temperature)
					if self.probe.temperature >= _step.temperature:
						print "YES"
						_step.active_time=now
				else:
					if self.probe.temperature <= _step.temperature:
						_step.active_time=now
			else:
				print "_step.active_time+timedelta(seconds=_step.hold_seconds)"
				print now
				print str(_step.active_time+timedelta(seconds=_step.hold_seconds))
				#check if we should move on to the next step
				if now>_step.active_time+timedelta(seconds=_step.hold_seconds):
					next=self.scheduleStep.filter(step_index=_step.index+1)
					print "next:" + str(next)
					if next:
						next = next[0]
						next.active=True
						_step.active=False
						_step.active_time=None


	def __unicode__(self):
		return self.name

# Each Probe.
class Probe(models.Model):
	owner = models.ForeignKey('auth.User', related_name='probes', blank=True, null=True)

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

	#the probe's current temperature in c
	temperature = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=6)

	#the probe's current target temperature. Returns c or f depending on the global units
	target_temperature = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=6)

	#the correction factor if neeced
	correction_factor = models.DecimalField(default=0.0, decimal_places=2,
											max_digits=6) #a correction factor to apply (if any)

	#the date of the last good reading for self.temperature
	last_temp_date = models.DateTimeField(null=True, blank=True) #time of this status

	#returns the current temperature of this probe.
	def getCurrentTemp(self, returnlatest=False):
		units = GlobalSettings.objects.get_setting('UNITS')

		if returnlatest and self.temperature:
			return self.temperature

		updateNeeded = True
		# we only update every 10 seconds. maybe this could be a global conf
		if self.last_temp_date and self.temperature:
			now = timezone.now()
			if now < self.last_temp_date + timedelta(seconds=10):
				updateNeeded = False

		if not updateNeeded:
			return self.temperature

		temp = None
		count = 0

		#wait 10 times to see if we get a good reading
		while count < 10 and not temp:

			try:
				f = open('/sys/bus/w1/devices/' + self.one_wire_Id + "/w1_slave", 'r')
				lines = f.readlines()
				crcline = lines[0]
				tempLine = lines[1]
				result_list = tempLine.split("=")
				count += 1
				if crcline.find("YES") > -1:
					temp = float(result_list[-1]) / 1000 # temp in Celcius

					if self.correction_factor is not None:
						temp += float(self.correction_factor)# correction factor

			except IOError:
				#print "Error: File " '/sys/bus/w1/devices/' + self.one_wire_Id + "/w1_slave does not exist.";
				temp = None
				break

		#this is now all done on the client side
		#if units.value == 'imperial':
		#	temp = (9.0/5.0)*float(temp) + 32  #convert to F

		if (self.temperature != temp):
			#update the last good date if we have a good reading
			if not temp is None:
				self.last_temp_date = timezone.now()

			self.temperature = temp
			self.save()

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
	power = models.IntegerField(default=100)
	enabled = models.BooleanField(default=True) #enabled
	

# An SSR has probe and PID information
class SSR(models.Model):
	owner = models.ForeignKey('auth.User', related_name='ssrs', blank=True, null=True)

	#an ssr is directly tied to a probe and a pid
	name = models.CharField(max_length=30)
	pin = models.IntegerField()
	probe = models.ForeignKey(Probe, null=True, related_name='ssrs')
	pid = models.OneToOneField(PID, null=True, related_name='ssrs')
	enabled = models.BooleanField(default=True) #enabled
	state = models.BooleanField(default=False) #on/off

	#these are updated on demand
	eta = models.FloatField(null=True, blank=True)
	degreesPerMinute = models.FloatField(null=True, blank=True)

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
		"""


		@return:
		"""
		eta=None
		degreesPerMinute=None
		#print "Get ETA:"
		#print str(self.pk) + " " + str(self.state)
		#print str(self.probe.target_temperature)
		#print str(self.probe.temperature)
		
		if self.probe.target_temperature and self.probe.temperature:
			#get the temps for this probe for the last 60 minutes
			now = timezone.now()
			
			#default to one hour
			startdate = now + timedelta(hours=-1)
			
			currentTemp=self.probe.temperature
			currentTemp=float(currentTemp)
				
			#filter when the ssr state is true
			statuses = Status.objects.filter(date__gte=startdate, date__lte=now, probes__ssrstatus__state=True)

			if statuses and len(statuses) >= 2:
				
				starttemp=None

				# first, find the starting probe status
				for status in statuses:
					if status.probes:
						try:
							pp = status.probes.get(probe__id=self.probe.id)
						except ProbeStatus.DoesNotExist:
							continue

					if (not starttemp) and pp.temperature:
						startdate=status.date
						starttemp=float(pp.temperature)
						break

				# find the difference between when we started and where we are now
				if starttemp and currentTemp:
					tempDiff=float(currentTemp)-float(starttemp)
					timeDiff=float((now-startdate).seconds)/60
					degreesPerMinute=0
					if timeDiff>0:
						degreesPerMinute=tempDiff/timeDiff
						
					#print "delta (min) %f" % timeDiff
					#print "%d : target: %f tempdiff: %f starttemp: %f currenttemp: %f dpm: %f" % (self.probe.pk , float(self.probe.target_temperature), float(tempDiff), float(startTemp), float(currentTemp), float(degreesPerMinute));

				# and now see how long it will take to get to the target temperature based on the degreesPerMinute
				if currentTemp and self.probe.target_temperature and degreesPerMinute:
					diff=float(self.probe.target_temperature)-currentTemp
					#print "diff: " + str(diff) + " degreesPerMinute:" + str(degreesPerMinute)
					eta=abs(diff/degreesPerMinute)
					#print "minutes: " + str(eta)
					#print "now: " + str(now)
					eta = now + timedelta(minutes=eta)
					eta = time.mktime(eta.timetuple())*1000
					self.eta = eta
					self.degreesPerMinute = degreesPerMinute
					self.save()

		return eta, degreesPerMinute
			
