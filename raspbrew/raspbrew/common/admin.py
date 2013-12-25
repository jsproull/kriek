from django.contrib import admin

# Register your models here.

from .models import Probe

class ProbeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Probe, ProbeAdmin)
