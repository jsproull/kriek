from django.db import models


# Create your models here.
class FermConfiguration(models.Model):
	owner = models.ForeignKey('auth.User', related_name='fermconfs')

	name = models.CharField(max_length=30)
	probes = models.ManyToManyField('common.Probe', null=True, blank=True)
	ssrs = models.ManyToManyField('common.SSR', null=True, blank=True)
	enabled = models.BooleanField(default=True)
	
	FERMENTATION_MODE = (
		(0, 'Fermentation Regular'),
		(1, 'Fermentation Coolbot'),
	)
	mode = models.IntegerField(default=0, choices=FERMENTATION_MODE)
		
	#a schedule for this brew session
	schedules = models.ManyToManyField('common.Schedule', null=True, blank=True)
	
	def __unicode__(self):
		return self.name
		
	class Meta:
		verbose_name = "Fermentation Configuration"
		verbose_name_plural = "Fermentation Configuration"
