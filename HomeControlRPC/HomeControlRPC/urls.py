from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^AC/', include('AC.urls')),
    url(r'^cam/', include('cam.urls')),
    url(r'^rhost/', include('rhost.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
