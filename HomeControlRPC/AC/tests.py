import re
import json
import urllib
from random import choice

import serial
from mock import Mock, call, create_autospec, patch
from django.utils import unittest
from django.core.urlresolvers import reverse
from  django.test import TestCase as DjangoTestCase
from django_nose import FastFixtureTestCase as TestCase

from . import get_path
import AC
from AC.models import AcControl

class RegExMatcher():
    def __init__(self, pattern):
        self.matcher = re.compile(pattern)
    
    def __eq__(self, second):
        print second
        match = self.matcher.match(second)
        return True if match else False
    
    def __unicode__(self):
        return u'a string matching "%s"' % (self.matcher.pattern)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    __repr__ = __unicode__

arduino_ac_valid_params = {
    'P': (0, 1),
    'M': (0, 1, 2, 3),
    'F': (0, 1, 2, 3),
    'T': range(20, 30),
}

class ArduinoGoldenModel():
    replies = list()
    
    def __init__(self, *args, **kwargs):
        self.replies = ['Arduino A/C-Control v1.0 - Ready\n']
    
    def readline(self):
        if self.replies:
            return self.replies.pop(0)
        else:
            raise serial.SerialTimeoutException()
    
    def write(self, str):
        assert(len(str) > 0)
        p = str[0]
        if p in arduino_ac_valid_params.keys():
            assert(len(str) > 1)
            v = int(str[1:])
            if v in arduino_ac_valid_params[p]:
                self.replies.append('%s parameter set to %d\n\r' % (p, v))
            else:
                self.replies.append('Invalid something')
        elif 'S' == p:
            self.replies.append('Sending A/C command with following '
                                'parameters: Power=?, Mode=?, Fan=?, '
                                'Temperature=??')
            self.replies.append('Success')

def _param_caller(ac):
    for cmd, valid_values in arduino_ac_valid_params.iteritems():
        for v in valid_values:
            ac.writeParam(cmd, v)
            AC.models.logger.debug.assert_called_with(
                                u'%s parameter set to %d' % (cmd, v))

class AcControlMockedMethodsTests(TestCase):
    
    def setUp(self):
        "Initializes mock AcControl object for tests"
        AC.models.logger = Mock()
        self.mock_ac = AcControl(name='Mock A/C', beep_timeout=3.0)
    
    def test_ac_repr(self):
        "Test the instance unicode representation is correct."
        self.assertEqual(unicode(self.mock_ac), u'Mock A/C (MOCK-SERIAL) #1')
    
    def test_mock_ac_is_default_ac(self):
        """
        isMockSerial() should return True for AcControl
        with default serial port.
        """
        self.assertTrue(self.mock_ac.isMockSerial())
    
    def test_mock_init_serial(self):
        """
        Check that initSerialPort() on mocked AcControl object
        doesn't raise an exception, a debug message is logged,
        and the _serial property is set to None.
        """
        try:
            self.mock_ac.initSerialPort()
        except Exception, ex:
            self.fail('initSerialPort() raised excecption "%s"' % (ex))
        self.assertIsNone(self.mock_ac._serial)
        AC.models.logger.debug.assert_called_with(
                    RegExMatcher(u'Arduino A\/C-Control v\d\.\d \- Ready'))
    
    def test_mock_write_param(self):
        """
        Check that writeParam() on mocked AcControl object
        doesn't raise exception, and a proper debug message is logged.
        """
        try:
            self.mock_ac.initSerialPort()
        except Exception, ex:
            self.fail('initSerialPort() raised excecption "%s"' % (ex))
        AC.models.logger.debug.assert_called_with(
                    RegExMatcher(u'Arduino A\/C-Control v\d\.\d \- Ready'))
        try:
            _param_caller(self.mock_ac)
        except Exception, ex:
            self.fail('writeParam() raised excecption "%s"' % (ex))
    
    def test_random_mock_recording(self):
        "Check that _get_mic_mock_file() returns an existing file"
        import os
        self.assertTrue(os.path.isfile(self.mock_ac._get_mic_mock_file()))
    
    def test_mock_send_command(self):
        """
        Check that sendCommand() on mocked AcControl object with multiple
        possible canned recordings functions as expected,
        including returned result string and log writes.
        """
        ac_commands = [
            (u'Success', get_path(u'test-data', 'beeps-1.raw'),
             u'Using mock file .*beep.*\.raw'),
            (u'Beep Timeout', get_path(u'test-data', 'noise.raw'),
             u'Using mock file .*noise.*\.raw'),
        ]
        for exp_res, mock_file, log_msg in ac_commands:
            params = {
                'pwr': str(choice(arduino_ac_valid_params['P'])),
                'mode': str(choice(arduino_ac_valid_params['M'])),
                'fan': str(choice(arduino_ac_valid_params['F'])),
                'temp': str(choice(arduino_ac_valid_params['T'])),
            }
            self.mock_ac._get_mic_mock_file = Mock(return_value=mock_file)
            self.assertEqual(self.mock_ac.sendCommand(params), exp_res)
            AC.models.logger.debug.assert_has_calls([
                call(RegExMatcher(u'Arduino A\/C-Control v\d\.\d \- Ready')),
                call(u'P parameter set to %s' % (params['pwr'])),
                call(u'M parameter set to %s' % (params['mode'])),
                call(u'F parameter set to %s' % (params['fan'])),
                call(u'T parameter set to %s' % (params['temp'])),
                call(RegExMatcher(log_msg)),
                call(u'Success'),
            ])
            AC.models.logger.debug.reset_mock()

class AcControlPseudoMockedMethodsTests(TestCase):
    
    def setUp(self):
        "Initializes AcControl object for tests"
        AC.models.logger = Mock()
        self.ac = AcControl(name='Pseudo Mock A/C', serial_port='not real',
                                 beep_timeout=3.0)
    
    def test_ac_repr(self):
        "Test the instance unicode representation is correct."
        self.assertEqual(unicode(self.ac),
                         u'Pseudo Mock A/C (not real) #1')
    
    def test_mock_ac_is_false(self):
        """
        isMockSerial() should return False for AcControl
        with specified serial port.
        """
        self.assertFalse(self.ac.isMockSerial())
    
    @patch('serial.Serial', autospec=True)
    def test_init_serial_good_port(self, mocked_serial):
        """
        Check that initSerialPort() on AcControl object
        doesn't raise an exception, a debug message is logged,
        and the _serial property is set.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        try:
            self.ac.initSerialPort()
        except Exception, ex:
            self.fail('initSerialPort() raised excecption "%s"' % (ex))
        mocked_serial.assert_called_once_with('not real', timeout=2.0)
        self.assertIsNotNone(self.ac._serial)
        AC.models.logger.debug.assert_has_calls([
            call('Initializing Pseudo Mock A/C (not real) #1'),
            call(RegExMatcher(u'Arduino A\/C-Control v\d\.\d \- Ready')),
        ])
    
    @patch('serial.Serial', autospec=True)
    def test_init_serial_bad_port(self, mocked_serial):
        """
        Check that calling initSerialPort with bad serial port
        raises serial exception.
        """
        mocked_serial.configure_mock(**{
            'side_effect': serial.SerialException('boom'),
        })
        self.assertRaises(serial.SerialException, self.ac.initSerialPort)

    def test_write_param_uninitialized_serial_error(self):
        "Check that writeParam() raises exception if serial port uninitialized"
        with self.assertRaisesRegexp(serial.SerialException,
                                     u'Serial port not initialized'):
            self.ac.writeParam('P', 0)
    
    @patch('serial.Serial', autospec=True)
    def test_write_param_invalid_value(self, mocked_serial):
        """
        Check that writeParam() raises a serial exception if an invalid param
        value is written, and that the Arduino response is logged.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        try:
            self.ac.initSerialPort()
        except Exception, ex:
            self.fail('initSerialPort() raised excecption "%s"' % (ex))
        for p in arduino_ac_valid_params.keys():
            with self.assertRaisesRegexp(serial.SerialException,
                                         u'Failed setting parameter %s '
                                         u'to value 9' % (p)):
                self.ac.writeParam(p, 9)
            AC.models.logger.debug.assert_called_with(
                                        RegExMatcher(u'Invalid .*'))
    
    def test_none_mock_recording(self):
        "Check that _get_mic_mock_file() returns None"
        self.assertIsNone(self.ac._get_mic_mock_file())
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_good(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with multiple
        possible canned recordings functions as expected,
        including returned result string and log writes.
        """
        ac_commands = [
            (u'Success', get_path(u'test-data', 'beeps-1.raw')),
            (u'Beep Timeout', get_path(u'test-data', 'noise.raw')),
        ]
        for exp_res, mock_file in ac_commands:
            mocked_serial.configure_mock(**{
                'return_value': ArduinoGoldenModel(),
            })
            params = {
                'pwr': str(choice(arduino_ac_valid_params['P'])),
                'mode': str(choice(arduino_ac_valid_params['M'])),
                'fan': str(choice(arduino_ac_valid_params['F'])),
                'temp': str(choice(arduino_ac_valid_params['T'])),
            }
            self.ac._get_mic_mock_file = Mock(return_value=mock_file)
            self.assertEqual(self.ac.sendCommand(params), exp_res)
            AC.models.logger.debug.assert_has_calls([
                call('Initializing Pseudo Mock A/C (not real) #1'),
                call(RegExMatcher(u'Arduino A\/C-Control v\d\.\d \- Ready')),
                call(u'P parameter set to %s' % (params['pwr'])),
                call(u'M parameter set to %s' % (params['mode'])),
                call(u'F parameter set to %s' % (params['fan'])),
                call(u'T parameter set to %s' % (params['temp'])),
                call(u'Sending A/C command with following parameters: '
                     u'Power=?, Mode=?, Fan=?, Temperature=??'),
                call(u'Success'),
            ])
            mocked_serial.reset_mock()
            AC.models.logger.debug.reset_mock()
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_bad_serial(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with bad serial port
        returns a "Serial Error" response string.
        """
        mocked_serial.configure_mock(**{
            'side_effect': serial.SerialException('boom'),
        })
        self.assertEqual(self.ac.sendCommand({}), u'Serial Error')
        AC.models.logger.debug.assert_called_with(
                                u'Serial port not real error: boom')
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_missing_param_1(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with missing parameter
        returns a "Missing Parameter" response string.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        self.assertEqual(self.ac.sendCommand({}),
                         u'Missing Parameter (\'pwr\')')
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_missing_param_2(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with missing parameter
        returns a "Missing Parameter" response string.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        self.assertEqual(self.ac.sendCommand({'pwr': '0'}),
                         u'Missing Parameter (\'mode\')')
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_missing_param_3(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with missing parameter
        returns a "Missing Parameter" response string.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        self.assertEqual(self.ac.sendCommand({'pwr': '0', 'mode': '0'}),
                         u'Missing Parameter (\'fan\')')
    
    @patch('serial.Serial', autospec=True)
    def test_send_command_missing_param_4(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with missing parameter
        returns a "Missing Parameter" response string.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        self.assertEqual(self.ac.sendCommand({'pwr': '0', 'mode': '0',
                                              'fan': '0'}),
                         u'Missing Parameter (\'temp\')')

    @patch('serial.Serial', autospec=True)
    def test_send_command_bad_param_type(self, mocked_serial):
        """
        Check that sendCommand() on AcControl object with bad parameter type
        returns a "Invalid Parameter" response string.
        """
        mocked_serial.configure_mock(**{
            'return_value': ArduinoGoldenModel(),
        })
        self.assertEqual(self.ac.sendCommand({'pwr': 'w00t', 'mode': '0',
                                              'fan': '0', 'temp': '25'}),
                         u'Invalid Parameter')

class AcCommnadViewTests(DjangoTestCase):
    
    def test_command_with_missing_params(self):
        """
        If no parameters are given,
        a "Missing Parameter" error should be returned.
        """
        response = self.client.get(reverse('ac-send-command'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/json')
        self.assertEqual(json.loads(response.content), u'Missing Parameter')
    
    def test_command_with_no_ac(self):
        """
        If no AcControl objects are present,
        a "No A/C Defined" error should be returned.
        """
        response = self.client.get('%s?%s' % (reverse('ac-send-command'),
                                   urllib.urlencode({'pwr': '0', 'mode': '0',
                                   'fan': '0', 'temp': '25'})))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/json')
        self.assertEqual(json.loads(response.content), u'No A/C Defined')
