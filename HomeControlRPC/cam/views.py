import logging
import json
import sys
import tempfile
from mimetypes import guess_type

from django.http import HttpResponse
from django.conf import settings

from cam.models import WebCam, is_file_image

logger = logging.getLogger(__name__)

def get_snapshot(request):
    "Take a webcam snapshot and return it as HTTP response"
    content_type = 'application/json'
    body = json.dumps('Failed snapshot')
    # Try every available WebCam object to take the snapshot,
    #  until the first one that succeeds
    for cam in WebCam.objects.all().order_by('priority'):
        logger.debug('Attempting saveSnapshot with %s' % (cam))
        snapshot_file = cam.saveSnapshot()
        if snapshot_file and is_file_image(snapshot_file):
            content_type, _ = guess_type(snapshot_file)
            if content_type:
                body = open(snapshot_file, 'rb').read()
                break
            else:
                content_type = 'application/json'
    return HttpResponse(body, content_type=content_type)
