from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe, SSR
import os

# Create your models here.
class BrewConfiguration(models.Model):
	name = models.CharField(max_length=30)
	probes = models.ManyToManyField(Probe)
	ssrs = models.ManyToManyField(SSR)
	
	def __unicode__(self):
		return self.name
		
	class Meta:
		verbose_name = "Brew Configuration"
		verbose_name_plural = "Brew Configuration"
		
	#TODO - add brew temp control over time
