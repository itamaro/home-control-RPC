from django.conf.urls import patterns, url

from cam import views

urlpatterns = patterns('',
    url(r'^snapshot/$', views.get_snapshot, name='cam-get-snapshot'),
)
