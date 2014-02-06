from django.db import models


# Create your models here.
class BrewConfiguration(models.Model):
	owner = models.ForeignKey('auth.User', related_name='brewconfs')

	name = models.CharField(max_length=30)
	probes = models.ManyToManyField('common.Probe', null=True, blank=True)
	ssrs = models.ManyToManyField('common.SSR', null=True, blank=True)
	enabled = models.BooleanField(default=True)
	
	#if this is set, we only allow one ssr to be fired at once
	#current_ssr = models.OneToOneField('common.SSR', related_name='current_ssr', null=True, blank=True)
	allow_multiple_ssrs = models.BooleanField(default=False)
	
	#a schedule for this brew session
	schedules = models.ManyToManyField('common.Schedule', null=True, blank=True)
	
	def __unicode__(self):
		return self.name

	class Meta:
		verbose_name = "Brew Configuration"
		verbose_name_plural = "Brew Configuration"

