# Modules selection section
ARDUINO_ENABLED =   True
CAM_ENABLED =       True

# WSGI HTTP server parameters
WsgiHost = ''
WsgiPort = 8000

# Serial port device ID where the Arduino is connected
# ('COM#' on Windows, some '/dev/tty*' on Linux)
# set to 'MOCK-SERIAL' in order to mock the serial port instead of a real one
SerialPortID = 'MOCK-SERIAL'

# Beep detection parameters
#  Timeout to wait for beep
BeepDetectionTimeout   = 1.5
#  Time to wait after starting mic-listening and before sending command.
PreDetectionWaitTime   = 0.2
# Set to full path of debug recording file
# If not None, the beep-detection recording will be saved to this file.
BeepDetectDebugRecFile = None

try:
    from local_settings import *
except ImportError:
    pass
