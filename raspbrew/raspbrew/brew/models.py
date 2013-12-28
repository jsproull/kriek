from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe, SSR
import os

# Create your models here.
class BrewConfiguration(models.Model):
	name = models.CharField(max_length=30)
	probes = models.ManyToManyField(Probe)
	ssrs = models.ManyToManyField(SSR)
	enabled = models.BooleanField(default=True)
	
	#if this is set, we only allow one ssr to be fired at once
	current_ssr = models.OneToOneField(SSR, related_name='current_ssr', null=True, blank=True)
	allow_multiple_ssrs = models.BooleanField(default=False)
	
	def __unicode__(self):
		return self.name
		
	class Meta:
		verbose_name = "Brew Configuration"
		verbose_name_plural = "Brew Configuration"
		
	#TODO - add brew temp control over time
