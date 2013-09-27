import sys
import serial
import time
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
    def __init__(self, serial_port, beep_timeout, listen_delay,
                 debug_rec_file=None):
        self.serial_port = serial_port
        self.beep_timeout = beep_timeout
        self.listen_delay = listen_delay
        self.debug_rec_file = debug_rec_file
        if self.isMockSerial():
            self.ser = None
            debug('Arduino A/C-Control v1.0 - Ready')
        else:
            # Initialize serial port
            # (let exceptions bubble up in case of serial errors)
            self.ser = serial.Serial(self.serial_port, timeout=2.0)
            debug(self.ser.readline())
    
    def isMockSerial(self):
        return 'MOCK-SERIAL' == self.serial_port
    
    def setParam(self, p, v):
        if self.ser:
            # Send command string via serial and get a line response
            self.ser.write('%s%d' % (p, v))
            res = self.ser.readline().strip()
        else:
            # Mocked behaviour - success
            res = '%s parameter set to %d' % (p, v)
        debug(res)
        if res.find('parameter set to') < 0:
            raise serial.SerialException(
                    'Failed setting parameter %s to value %d' % (p, v))
    
    def sendSend(self):
        analyzer = MicAnalyzer()
        mock_file = None
        if not self.ser:
            # Mocked behaviour - randomized success / beep-timeout
            #  (using the microphone analyzer, with canned recording)
            response = 'Success'
            from random import choice
            mock_file = choice(['test-data/noise.raw',
                                'test-data/beeps-1.raw'])
            debug('Using mock file %s' % (mock_file))
        # Activate mic-listening and send the "Send" command via serial
        analyzer.start_listen(self.beep_timeout, rec_file=mock_file,
                              debug_rec_file=self.debug_rec_file)
        time.sleep(self.listen_delay)
        if self.ser:
            self.ser.write('S')
            # Dummy-read a line-response, and store the interesting response
            debug(self.ser.readline().strip())
            response = self.ser.readline().strip()
        debug(response)
        # Wait for beep
        if 'Success' == response and not analyzer.is_beep():
            response = 'Beep Timeout'
        return response
            
    def sendCommand(self, params):
        try:
            self.setParam('P', PowerDict[params['pwr'][0]])
            self.setParam('M', ModeDict[params['mode'][0]])
            self.setParam('F', FanDict[params['fan'][0]])
            self.setParam('T', int(params['temp'][0]))
            response = self.sendSend()
        except serial.SerialException, ex:
            debug('Serial port %s error: %s' %
                    (self.serial_port, ex))
            response = 'Serial Error'
        except KeyError, ex:
            response = 'Unsupported Parameter Value %s' % (ex)
            debug(response)
        return response
