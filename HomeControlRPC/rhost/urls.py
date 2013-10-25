from django.conf.urls import patterns, url

from rhost import views

urlpatterns = patterns('',
    url(r'^list-hosts/$', views.list_hosts, name='rhost-list-hosts'),
    url(r'^check-power/(?P<host_name>[\w\-]+)/$', views.check_power, name='rhost-check-power'),
    url(r'^list-vms/(?P<host_name>[\w\-]+)/$', views.list_vms, name='rhost-list-vms'),
    url(r'^check-power/(?P<host_name>[\w\-]+)/(?P<vmid>\d+)/$', views.check_vm_power, name='rhost-check-vm-power'),
    url(r'^turn-on/(?P<host_name>[\w\-]+)/(?P<vmid>\d+)/$', views.turn_on_vm, name='rhost-turn-on-vm'),
    url(r'^shutdown/(?P<host_name>[\w\-]+)/(?P<vmid>\d+)/$', views.shutdown_vm, name='rhost-shutdown-vm'),
    url(r'^turn-on/(?P<host_name>[\w\-]+)/$', views.turn_on_host, name='rhost-turn-on-host'),
    url(r'^shutdown/(?P<host_name>[\w\-]+)/$', views.shutdown_host, name='rhost-shutdown-host'),
)
