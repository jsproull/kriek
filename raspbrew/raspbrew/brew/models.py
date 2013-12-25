from django.db import models
from raspbrew import settings
from raspbrew.common.models import Probe
import os

# Create your models here.
class Config(models.Model):
	probes = models.ManyToManyField(Probe)
	

