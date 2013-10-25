import logging
import json
import time
from collections import defaultdict
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core import serializers

from rhost.models import RemoteHost, SshHost, EsxiHost

logger = logging.getLogger(__name__)

def list_hosts(request):
    "Return a dictionary of host-types with lists of hosts per type"
    hosts = defaultdict(list)
    visited = set()
    models = [EsxiHost, SshHost, RemoteHost]
    for model in models:
        mhosts = model.objects.all().reverse()
        for host in mhosts:
            if host.pk in visited:
                continue
            visited.add(host.pk)
            model_name = type(host).__name__.split('.')[-1]
            hosts[model_name].append((host.name, host.ip_address))
    return HttpResponse(json.dumps(hosts),
                        content_type='application/json')

def check_power(request, host_name):
    "Return power status of requested host (ON/OFF string)"
    host = get_object_or_404(RemoteHost, name=host_name)
    power_state = host.isHostUp() and 'ON' or 'OFF'
    return HttpResponse(json.dumps({host.name: power_state}),
                        content_type='application/json')

def list_vms(request, host_name):
    "Return list of virtual machines of requested ESXi host"
    host = get_object_or_404(EsxiHost, name=host_name)
    vms = host.listVirtualMachines()
    return HttpResponse(json.dumps({host.name: vms}),
                        content_type='application/json')

def check_vm_power(request, host_name, vmid):
    "Return power status of requested VM on ESXi host"
    host = get_object_or_404(EsxiHost, name=host_name)
    try:
        power_state = host.isVirtualMachineUp(vmid) and 'ON' or 'OFF'
    except RuntimeError:
        power_state = 'No Such VM'
    return HttpResponse(json.dumps({vmid: power_state}),
                        content_type='application/json')

def turn_on_vm(request, host_name, vmid):
    "Turn on a virtual machine on ESXi host"
    host = get_object_or_404(EsxiHost, name=host_name)
    try:
        power_on = host.turnOnVirtualMachine(vmid)
    except RuntimeError:
        pass
    time.sleep(1.0)
    # TODO: changeme
    return HttpResponse(json.dumps({vmid: 'ON'}),
                        content_type='application/json')
    return check_vm_power(request, host_name, vmid)

def shutdown_vm(request, host_name, vmid):
    "Shutdown a virtual machine on ESXi host"
    host = get_object_or_404(EsxiHost, name=host_name)
    try:
        shutdown = host.shutdownVirtualMachine(vmid)
    except RuntimeError:
        pass
    time.sleep(1.0)
    # TODO: changeme
    return HttpResponse(json.dumps({vmid: 'OFF'}),
                        content_type='application/json')
    return check_vm_power(request, host_name, vmid)

def turn_on_host(request, host_name):
    "Turn on a host"
    host = get_object_or_404(RemoteHost, name=host_name)
    power_state = host.powerOn() and 'ON' or 'OFF'
    return HttpResponse(json.dumps({host.name: power_state}),
                        content_type='application/json')

def shutdown_host(request, host_name):
    "Shutdown a host"
    host = get_object_or_404(RemoteHost, name=host_name)
    power_state = host.get_specialized_instance().shutdown() and 'OFF' or 'ON'
    return HttpResponse(json.dumps({host.name: power_state}),
                        content_type='application/json')
