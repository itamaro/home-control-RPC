import sys
import serial
from mic import MicAnalyzer

def debug(s):
    print 'ARDUINO::\t %s' % (s)

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

class AcControl(object):
    def __init__(self, serial_port, mock_serial=False):
        self.serial_port = serial_port
        self.mock_serial = mock_serial
        if self.mock_serial:
            self.ser = None
            debug('Arduino A/C-Control v1.0 - Ready')
        else:
            try:
                self.ser = serial.Serial(self.serial_port, timeout=1.0)
                debug(self.ser.readline())
            except serial.SerialException, ex:
                debug('Failed opening serial port %s: %s' %
                        (self.serial_port, ex))
                self.ser = None
    
    def setParam(self, p, v):
        if self.mock_serial:
            res = 'Some parameter set to %d' % (v)
        elif self.ser:
            self.ser.write('%s%d' % (p, v))
            res = self.ser.readline().strip()
        else:
            response = 'Serial Error'
        debug(res)
        if res.find('parameter set to') < 0:
            raise serial.SerialException(
                    'Failed setting parameter %s to value %d' % (p, v))
    
    def sendSend(self, beep_timeout):
        analyzer = MicAnalyzer()
        mock_file = None
        if self.mock_serial:
            response = 'Success'
            from random import choice
            mock_file = choice(['test-data/noise.raw',
                                'test-data/beeps-1.raw'])
            debug('Using mock file %s' % (mock_file))
        elif self.ser:
            analyzer.start_listen(beep_timeout)
            self.ser.write('S')
            debug(self.ser.readline().strip())
            response = self.ser.readline().strip()
        else:
            response = 'Serial Error'
        debug(response)
        if 'Success' == response and not analyzer.is_beep(beep_timeout,
                                                          mock_file):
            response = 'Beep Timeout'
        return response
            
    def sendCommand(self, params, beep_timeout=2.0):
        try:
            self.setParam('P', PowerDict[params['pwr'][0]])
            self.setParam('M', ModeDict[params['mode'][0]])
            self.setParam('F', FanDict[params['fan'][0]])
            self.setParam('T', int(params['temp'][0]))
            response = self.sendSend(beep_timeout)
        except serial.SerialException, ex:
            debug('Serial port %s error: %s' %
                    (self.serial_port, ex))
            response = 'Serial Error'
        except KeyError, ex:
            response = 'Unsupported Parameter Value %s' % (ex)
            debug(response)
        return response
