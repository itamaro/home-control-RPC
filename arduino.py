import sys
import serial

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
            
    def sendCommand(self):
        if self.mock_serial:
            response = 'test\r\n'
        elif self.ser:
            try:
                self.ser.write('t')
                response = self.ser.readline()
            except serial.SerialException, ex:
                print 'ARDUINO::    Failed writing to serial port %s: %s' %  \
                        (self.serial_port, ex)
                response = 'Serial Error'
        else:
            return 'Serial Error'
        return response.strip()
