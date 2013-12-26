from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe, SSR
import os

# Create your models here.
class BrewConfiguration(models.Model):
	probes = models.ManyToManyField(Probe)
	ssrs = models.ManyToManyField(SSR)
	

