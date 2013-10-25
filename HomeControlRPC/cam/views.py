import logging
import json
import sys
import tempfile
from django.http import HttpResponse
from django.conf import settings

from cam.models import WebCam

logger = logging.getLogger(__name__)

cam = None
if 'cam' in settings.INSTALLED_APPS:
    cam = WebCam()

def get_snapshot(request):
    "Take a webcam snapshot and return it as HTTP response"
    return HttpResponse(open(cam.saveSnapshot(), 'rb').read(),
                        content_type='image/png')
