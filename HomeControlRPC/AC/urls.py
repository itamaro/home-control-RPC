from django.conf.urls import patterns, url

from AC import views

urlpatterns = patterns('',
    url(r'^command/$', views.send_command, name='ac-send-command'),
)
