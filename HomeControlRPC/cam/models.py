import sys
import tempfile
import time
import logging

from django.db import models

logger = logging.getLogger(__name__)

WIN = LINUX = False
if 'win32' == sys.platform:
    WIN = True
    from VideoCapture import Device
else:
    LINUX = True
    import subprocess
    GST_COMMAND = 'gst-launch-0.10'

class WebCam(object):
    def __init__(self, outfilename=None):
        if outfilename:
            self.outfilename = outfilename
        else:
            outfile = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.outfilename = outfile.name
            outfile.close()
        if WIN:
            self.cam = Device()
        elif LINUX:
            self.callargs = [GST_COMMAND, '-v', 'v4l2src', '!',
                             #'video/x-raw-yuv,width=320,height=240,framerate=20/1', '!',
                             'decodebin', '!', 'ffmpegcolorspace', '!', 'pngenc',
                             '!', 'filesink', 'location="%s"' % (self.outfilename)]
            
    def saveSnapshot(self):
        if WIN:
            self.cam.saveSnapshot(self.outfilename)
        elif LINUX:
            if 0 != subprocess.call(self.callargs):
                return False
        return self.outfilename
