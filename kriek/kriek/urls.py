from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from django.conf.urls import include
from rest_framework.routers import DefaultRouter

from kriek import settings
from kriek import views, views_rest


#rest router
router = DefaultRouter()
router.register(r'probes', views_rest.ProbeViewSet)
router.register(r'users', views_rest.UserViewSet)
router.register(r'ssrs', views_rest.SSRViewSet)
router.register(r'pids', views_rest.PIDViewSet)
router.register(r'ferms', views_rest.FermConfViewSet)
router.register(r'brews', views_rest.BrewConfViewSet)
router.register(r'schedules', views_rest.ScheduleViewSet)
router.register(r'scheduleSteps', views_rest.ScheduleStepViewSet)

#router.register(r'users', views.UserViewSet)

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', TemplateView.as_view(template_name='index.html'), name="index"),
    url(r'^ferm$', views.ferm, {}, name='ferm'),
    url(r'^brew$', views.brew, {}, name='brew'),

    #rest calls
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^status/', views_rest.StatusList.as_view()),
    #url(r'^probes/$', views_rest.ProbeList.as_view()),
    #url(r'^probes/(?P<pk>[0-9]+)/$', views_rest.ProbeDetail.as_view()),

    #admin
    url(r'^admin/', include(admin.site.urls)),

    #login/logout
    url(r'^login$', views.login_view, {}, name='loginView'),
    url(r'^logout$', views.logout_view, {}, name='logoutView'),
    url(r'^accounts/login/$', TemplateView.as_view(template_name='index.html')), # 'django.contrib.auth.views.login'),

    #update
    #url(r'^update$', views.update, {}, name='update'),
    
    #all temp statuses
    #url(r'^status/(?P<numberToReturn>\d+)$', views.jsonStatus, {}, name='jsonStatus'),
    #url(r'^status/(?P<numberToReturn>\d+)/(?P<startDate>[0-9.]+)$', views.jsonStatus, {}, name='jsonStatus_withStartDate'),
    #url(r'^status/(?P<numberToReturn>\d+)/(?P<startDate>[0-9.]+)/(?P<endDate>[0-9.]+)$', views.jsonStatus, {}, name='jsonStatus_withDate'),
    
    #ferm temp status
    #url(r'^status/ferm/(?P<fermConfId>\d+)/(?P<numberToReturn>[0-9.]+)$', views.jsonFermStatus, {}, name='jsonFermStatus'),
    #url(r'^status/ferm/(?P<fermConfId>\d+)/(?P<numberToReturn>[0-9.]+)/(?P<startDate>[0-9.]+)$', views.jsonFermStatus, {}, name='jsonFermStatus_withStartDate'),
    #url(r'^status/ferm/(?P<fermConfId>\d+)/(?P<numberToReturn>[0-9.]+)/(?P<startDate>[0-9.]+)/(?P<endDate>[0-9.]+)$', views.jsonFermStatus, {}, name='jsonFermStatus_withDate'),
    
    #brew temp status
    #url(r'^status/brew/(?P<brewConfId>\d+)/(?P<numberToReturn>[0-9.]+)$', views.jsonBrewStatus, {}, name='jsonBrewStatus'),
    #url(r'^status/brew/(?P<brewConfId>\d+)/(?P<numberToReturn>[0-9.]+)/(?P<startDate>[0-9.]+)$', views.jsonBrewStatus, {}, name='jsonBrewStatus_withStartDate'),
    #url(r'^status/brew/(?P<brewConfId>\d+)/(?P<numberToReturn>[0-9.]+)/(?P<startDate>[0-9.]+)/(?P<endDate>[0-9.]+)$', views.jsonBrewStatus, {}, name='jsonBrewStatus_withDate'),
    
    #system conf
    url(r'^system/status/$', views.system_status, {}, name='system_status'),
    
    #static content
    url(r'^js/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/js'}),
    url(r'^css/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/css'}),

)
