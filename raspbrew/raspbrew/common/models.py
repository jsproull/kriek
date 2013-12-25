from django.db import models

# Create your models here.
class Probe(models.Model):
	probe_id = models.CharField(max_length=30)
	probe_name = models.CharField(max_length=30)
	temperature = models.IntegerField()  #returns c or f depending on the global units

class SSR(models.Model):
	HEATER_OR_CHILLER = (
		(0, 'Heater'),
		(1, 'Chiller'),
	)
	pin = models.IntegerField()
	heater_or_chiller = models.IntegerField(default=0, choices=HEATER_OR_CHILLER)
	
class Configuration(models.Model):
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

class CurrentStatus(models.Model):
	probe_id = models.CharField(max_length=10000)