import time
import logging

from django.db import models
import serial

from . import get_path
from mic import MicAnalyzer

logger = logging.getLogger(__name__)

PowerDict = {
    'Toggle': 0,
    'Leave': 1,
    }
ModeDict = {
    'Cool': 0,
    'Heat': 1,
    'Fan': 2,
    'Dry': 3,
    }
FanDict = {
    'Auto': 0,
    'Low': 1,
    'Medium': 2,
    'High': 3,
    }

class AcControl(models.Model):
    # Serial port device ID where the Arduino is connected
    # ('COM#' on Windows, some '/dev/tty*' on Linux)
    # set to 'MOCK-SERIAL' to mock the serial port instead of using a real one
    serial_port = models.CharField(max_length=50, default=u'MOCK-SERIAL')
    
    # Beep detection parameters
    #  Timeout to wait for beep
    beep_timeout = models.FloatField(default=1.5)
    
    #  Time to wait after starting mic-listening and before sending command.
    listen_delay = models.FloatField(default=0.2)
    
    # Set to full path of debug recording file
    # If not None, the beep-detection recording will be saved to this file.
    debug_rec_file = models.CharField(max_length=255, blank=True)
    
    _serial = None
    
    def __unicode__(self):
        return u'%s(%s)' % (self.__class__.__name__, self.serial_port)
    
    def isMockSerial(self):
        return u'MOCK-SERIAL' == self.serial_port
    
    def initSerialPort(self):
        if self.isMockSerial():
            self._serial = None
            logger.debug(u'Arduino A/C-Control v1.0 - Ready')
        else:
            # Initialize serial port
            # (let exceptions bubble up in case of serial errors)
            logger.debug('Initializing %s' % (self))
            self._serial = serial.Serial(self.serial_port, timeout=2.0)
            logger.debug(self._serial.readline())
    
    def writeParam(self, p, v):
        if self._serial:
            # Send command string via serial and get a line response
            self._serial.write('%s%d' % (p, v))
            res = unicode(self._serial.readline().strip())
        elif self.isMockSerial():
            # Mocked behaviour - success
            res = u'%s parameter set to %d' % (p, v)
        else:
            raise serial.SerialException(u'Serial port not initialized')
        logger.debug(res)
        if res.find(u'parameter set to') < 0:
            raise serial.SerialException(
                    u'Failed setting parameter %s to value %d' % (p, v))
    
    def writeSendAndListen(self):
        analyzer = MicAnalyzer()
        mock_file = get_path(u'test-data', 'beeps-1.raw')
        if self.isMockSerial():
            # Mocked behaviour - randomized success / beep-timeout
            #  (using the microphone analyzer, with canned recording)
            res = u'Success'
            from random import choice
            mock_file = choice([get_path(u'test-data', 'noise.raw'),
                                get_path(u'test-data', 'beeps-1.raw')])
            logger.debug(u'Using mock file %s' % (mock_file))
        # Activate mic-listening and send the "Send" command via serial
        analyzer.start_listen(self.beep_timeout, rec_file=mock_file,
                              debug_rec_file=self.debug_rec_file)
        time.sleep(self.listen_delay)
        if self._serial:
            self._serial.write('S')
            # Dummy-read a line-response, and store the interesting response
            logger.debug(self._serial.readline().strip())
            res = self._serial.readline().strip()
        logger.debug(res)
        # Wait for beep
        if u'Success' == res and not analyzer.is_beep():
            res = u'Beep Timeout'
        return res
    
    def sendCommand(self, params):
        try:
            self.initSerialPort()
            self.writeParam('P', PowerDict[params['pwr']])
            self.writeParam('M', ModeDict[params['mode']])
            self.writeParam('F', FanDict[params['fan']])
            self.writeParam('T', int(params['temp']))
            res = self.writeSendAndListen()
        except serial.SerialException, ex:
            logger.debug(u'Serial port %s error: %s' % (self.serial_port, ex))
            res = u'Serial Error'
        except KeyError, ex:
            res = u'Unsupported Parameter Value %s' % (ex)
            logger.debug(res)
        return res