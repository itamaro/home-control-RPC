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
    def __init__(self, serial_port):
        self.serial_port = serial_port
        if self.isMockSerial():
            self.ser = None
            debug('Arduino A/C-Control v1.0 - Ready')
        else:
            # Initialize serial port
            # (let exceptions bubble up in case of serial errors)
            self.ser = serial.Serial(self.serial_port, timeout=1.0)
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
    
    def sendSend(self, beep_timeout):
        analyzer = MicAnalyzer()
        mock_file = None
        if self.ser:
            # Activate mic-listening and send the "Send" command via serial
            analyzer.start_listen(beep_timeout)
            self.ser.write('S')
            # Dummy-read a line-response, and store the interesting response
            debug(self.ser.readline().strip())
            response = self.ser.readline().strip()
        else:
            # Mocked behaviour - randomized success / beep-timeout
            #  (using the microphone analyzer, with canned recording)
            response = 'Success'
            from random import choice
            mock_file = choice(['test-data/noise.raw',
                                'test-data/beeps-1.raw'])
            debug('Using mock file %s' % (mock_file))
        debug(response)
        # Wait for beep
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
