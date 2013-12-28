from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe, SSR
import os

# Create your models here.
class FermConfiguration(models.Model):
	name = models.CharField(max_length=30)
	probes = models.ManyToManyField(Probe)
	ssrs = models.ManyToManyField(SSR)
	enabled = models.BooleanField(default=True)
	
	FERMENTATION_MODE = (
		(0, 'Fermentation Regular'),
		(1, 'Fermentation Coolbot'),
	)
	mode = models.IntegerField(default=0, choices=FERMENTATION_MODE)
	
	def __unicode__(self):
		return self.name
		
	class Meta:
		verbose_name = "Fermentation Configuration"
		verbose_name_plural = "Fermentation Configuration"
		
	#TODO - add fermentation temp control over time