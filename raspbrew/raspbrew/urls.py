from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from raspbrew import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'raspbrew.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin2/', include(admin.site.urls)),
 
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="index"),

    #static content
    url(r'^js/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/js'}),
    url(r'^css/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/css'}),

)
