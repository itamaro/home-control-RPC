# Modules selection section
ARDUINO_ENABLED =   True
CAM_ENABLED =       True

# WSGI HTTP server parameters
WsgiHost = ''
WsgiPort = 8000

# Serial port device ID where the Arduino is connected
# ('COM#' on Windows, some '/dev/tty*' on Linux)
# set to 'MOCK-SERIAL' in order to use a mock serial port instead of a real one
SerialPortID = 'MOCK-SERIAL'

try:
    from local_settings import *
except ImportError:
    pass
