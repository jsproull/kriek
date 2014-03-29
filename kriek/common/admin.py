from django.contrib import admin

# Common models between brewing and fermentation

from .models import Probe
from .models import SSR
from .models import Schedule, ScheduleTime, ScheduleStep
from kriek.globalsettings.models import GlobalSettings

class ProbeAdmin(admin.ModelAdmin):
	pass
admin.site.register(Probe, ProbeAdmin)


class SSRAdmin(admin.ModelAdmin):
	fields = ('name', 'manual_mode', 'pwm_mode', 'enabled', 'pin', 'heater_or_chiller', 'probe', 'owner', 'reverse_polarity')
admin.site.register(SSR, SSRAdmin)


class GlobalSettingsAdmin(admin.ModelAdmin):
	pass
admin.site.register(GlobalSettings, GlobalSettingsAdmin)


class ScheduleAdmin(admin.ModelAdmin):
	pass
admin.site.register(Schedule, ScheduleAdmin)


class ScheduleTimeAdmin(admin.ModelAdmin):
	pass
admin.site.register(ScheduleTime, ScheduleTimeAdmin)


class ScheduleStepAdmin(admin.ModelAdmin):
	fields = ('name', 'step_index', 'start_temperature', 'end_temperature', 'active', 'hold_seconds')
admin.site.register(ScheduleStep, ScheduleStepAdmin)
