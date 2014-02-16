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
	url(r'^help$', TemplateView.as_view(template_name='help.html'), name="help"),
	url(r'^about$', TemplateView.as_view(template_name='about.html'), name="about"),

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

    #update global settings
    url(r'^update_global_setting', views.update_global_setting, {}, name='update_global_setting'),

    #system conf
    url(r'^system/status/$', views.system_status, {}, name='system_status'),
    
    #static content
    url(r'^js/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/js'}),
    url(r'^css/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL + '/css'}),

)
