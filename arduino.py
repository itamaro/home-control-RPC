import sys
import serial
from mic import MicAnalyzer

class AcControl(object):
    def __init__(self, serial_port, mock_serial=False):
        self.serial_port = serial_port
        self.mock_serial = mock_serial
        if self.mock_serial:
            self.ser = None
            print 'ARDUINO::    Welcome!'
        else:
            # TODO: Add timers to readlines...
            try:
                self.ser = serial.Serial(self.serial_port)
                print 'ARDUINO::    %s' % (self.ser.readline())
                print 'ARDUINO::    %s' % (self.ser.readline())
                print 'ARDUINO::    %s' % (self.ser.readline())
                print 'ARDUINO::    %s' % (self.ser.readline())
            except serial.SerialException, ex:
                print 'ARDUINO::    Failed opening serial port %s: %s' %  \
                        (self.serial_port, ex)
                self.ser = None
            
    def sendCommand(self, params, beep_timeout=2.0):
        analyzer = MicAnalyzer()
        mock_file = None
        if self.mock_serial:
            response = 'test\r\n'
            from random import choice
            mock_file = choice(['test-data/noise.raw',
                                'test-data/beeps-1.raw'])
            print 'Using mock file', mock_file
        elif self.ser:
            try:
                analyzer.start_listen(beep_timeout)
                self.ser.write('t')
                response = self.ser.readline()
            except serial.SerialException, ex:
                print 'ARDUINO::    Failed writing to serial port %s: %s' %  \
                        (self.serial_port, ex)
                response = 'Serial Error'
        else:
            response = 'Serial Error'
        if 'test' == response.strip():
            response = 'Success' if analyzer.is_beep(beep_timeout,
                                            mock_file) else 'Beep Timeout'
        return response
