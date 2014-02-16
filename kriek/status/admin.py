from django.contrib import admin

# Register your models here.

from .models import Status, ProbeStatus, SSRStatus, PIDStatus


class StatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(Status, StatusAdmin)


class ProbeStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(ProbeStatus, ProbeStatusAdmin)


class SSRStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(SSRStatus, SSRStatusAdmin)


class PIDStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(PIDStatus, PIDStatusAdmin)