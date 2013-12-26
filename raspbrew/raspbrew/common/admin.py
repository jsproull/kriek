from django.contrib import admin

# Common models between brewing and fermentation

from .models import Probe
from .models import SSR
from .models import GlobalConfiguration

class ProbeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Probe, ProbeAdmin)

class SSRAdmin(admin.ModelAdmin):
	fields = ('name', 'pin', 'heater_or_chiller', 'probe')
admin.site.register(SSR, SSRAdmin)

class GlobalConfigurationAdmin(admin.ModelAdmin):
    pass
admin.site.register(GlobalConfiguration, GlobalConfigurationAdmin)

