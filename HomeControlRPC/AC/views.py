import logging
import json
from django.http import HttpResponse
from django.conf import settings

from AC.models import AcControl

logger = logging.getLogger(__name__)

def send_command(request):
    "Send an A/C command via Arduino and return response from Arduino"
    if set(['mode', 'fan', 'temp', 'pwr']).issubset(request.GET.keys()):
        # Try every available AcControl object to send the command,
        #  until the first one that succeeds
        for ac_control in AcControl.objects.all():
            logger.debug('Attempting sendCommand with %s' % (ac_control))
            res = ac_control.sendCommand(request.GET)
            if u'Success' == res:
                break
    else:
        res = u'Missing Parameter'
    return HttpResponse(json.dumps(res), content_type='application/json')
