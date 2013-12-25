from django.db import models

# Create your models here.
class Probe(models.Model):
	probe_id = models.CharField(max_length=30)
	probe_name = models.CharField(max_length=30)
	

