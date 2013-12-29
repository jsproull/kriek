from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from raspbrew import settings
from raspbrew import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'raspbrew.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin2/', include(admin.site.urls)),
 
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="index"),
    url(r'^ferm$', views.ferm, {'something': 'template1.html'}, name='ferm'),
	url(r'^brew$', views.brew, {'something': 'template1.html'}, name='brew'),
	
	url(r'^status/(?P<numberToReturn>\d+)$', views.jsonStatus, {}, name='jsonStatus'),
	url(r'^status/(?P<numberToReturn>\d+)/(?P<startDate>\d+)$', views.jsonStatus, {}, name='jsonStatus_withStartDate'),
	url(r'^status/(?P<numberToReturn>\d+)/(?P<startDate>\d+)/(?P<endDate>\d+)$', views.jsonStatus, {}, name='jsonStatus_withDate'),
	#url(r'^status/(?P<numberToReturn>\d+)$', views.brewStatus, {}, name='brewStatus'),

    #static content
    url(r'^js/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/js'}),
    url(r'^css/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/css'}),

)
