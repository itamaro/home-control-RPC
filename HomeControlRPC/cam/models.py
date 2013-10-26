import sys
import os
import tempfile
import time
import logging

from django.db import models

logger = logging.getLogger(__name__)

WIN = LINUX = False
if 'win32' == sys.platform:
    WIN = True
    from VideoCapture import Device
    DEFAULT_DEV = '0'
else:
    LINUX = True
    import subprocess
    DEFAULT_DEV = 'gst-launch-0.10'

def is_file_image(path):
    return os.path.isfile(path) and   \
           os.path.splitext(path)[-1].lower() in ('.png', '.jpg', '.gif')
    
def _get_tmp_filename():
    tmpfile = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmpfile.close()
    return tmpfile.name

class WebCam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    # The priority for using when sending commands (lower value = higher priority)
    priority = models.PositiveIntegerField(default=1)
    
    # If an image file - will use as mocked response instead of actual webcam.
    # In Windows, value to pass to VideoCapture.Device (as string).
    # In Linux, gst-launch command name to execute for webcam capture.
    webcam_source = models.CharField(max_length=255,
                                     default=DEFAULT_DEV)
                                     #default='cam/test-data/SumoNoona.png')
    
    # Where to store snapshots from the webcam.
    #  Requires write access, obviously...
    #  Leave blank to use randomly generated temporary files.
    snapshot_file = models.CharField(max_length=255, blank=True, default='')
    
    def __unicode__(self):
        return u'%s #%d' % (self.name, self.priority)
    
    def saveSnapshot(self):
        if is_file_image(self.webcam_source):
            logger.debug('%s returning mock image file "%s"' %
                         (self, self.webcam_source))
            return self.webcam_source
        snapshot_file = self.snapshot_file
        if not snapshot_file:
            snapshot_file = _get_tmp_filename()
            logger.debug('Using temporary file "%s"' % (snapshot_file))
        if WIN:
            try:
                cam = Device(int(self.webcam_source))
                cam.saveSnapshot(snapshot_file)
                time.sleep(1.0)
                cam.saveSnapshot(snapshot_file)
            except Exception:
                return ''
        elif LINUX:
            callargs = [self.webcam_source, '-v', 'v4l2src', '!',
                        'decodebin', '!', 'ffmpegcolorspace', '!', 'pngenc',
                        '!', 'filesink', 'location="%s"' % (snapshot_file)]
            if 0 != subprocess.call(callargs):
                return ''
        return snapshot_file
