import os
import argparse
import urlparse
from wsgiref.simple_server import make_server
from settings import *

parser = argparse.ArgumentParser(description=
                                 'Home Control RPC auxiliary server.')
parser.add_argument('--host', default=WsgiHost,
                    help='Host name for WSGI server')
parser.add_argument('-p', '--port', type=int, default=WsgiPort,
                    help='Port for WSGI server')
parser.add_argument('-s', '--serial', default=SerialPortID,
                    help='Serial port where Arduino is connected')
parser.add_argument('-d', '--debug', action='store_true',
                    help='Enable debug server')

arduino = cam = None

def application(
        # environ points to a dictionary containing CGI like env-variables
        # which is filled by the server for each received request
        environ,
        # start_response is a callback function supplied by the server
        # which will be used to send the HTTP status and headers to the server
        start_response):
    # Extract relevant variables from the request
    pathinfo = environ['PATH_INFO']
    qs = environ['QUERY_STRING']
    cmd_params = urlparse.parse_qs(qs)
    if '/webcam.png' == pathinfo and cam:
        status = '200 OK'
        # Take a snapshot with the Cam module and send it over HTTP
        response_headers = [('Content-Type', 'image/png'),]
        start_response(status, response_headers)
        return open(cam.saveSnapshot(), 'rb').read()
    elif '/ac-command' == pathinfo and arduino:
        status = '200 OK'
        if set(['mode', 'fan', 'temp', 'pwr'])  \
                .issubset(cmd_params.keys()):
            # All parameters are present - send to Arduino module
            response_body = arduino.sendCommand(cmd_params)
        else:
            response_body = 'Missing Parameter'
    elif '/favicon.ico' == pathinfo:
        status = '404 Not Found'
        response_body = 'Not Found'
    elif args.debug:
        status = '200 OK'
        # Sorting and stringifying the environment key, value pairs
        response_body = ['%s: %s' % (key, value)
                        for key, value in sorted(environ.items())]
        response_body = '\n'.join(response_body)
    else:
        status = '403 Forbidden'
        response_body = 'Not Authorized'
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

if '__main__' == __name__:
    args = parser.parse_args()
    
    # Initialize enabled modules
    if CAM_ENABLED:
        from webcam import WebCam
        cam = WebCam()
        cam.saveSnapshot()

    if ARDUINO_ENABLED:
        from arduino import AcControl
        arduino = AcControl(args.serial, BeepDetectionTimeout,
                            PreDetectionWaitTime, BeepDetectDebugRecFile)
        
    # Instantiate the WSGI server.
    # It will receive the request, pass it to the application
    # and send the application's response to the client
    httpd = make_server(
       args.host,  # The host name.
       args.port,  # A port number where to wait for the request.
       application # Our application object name, in this case a function.
       )
    print "Serving HTTP on port %d..." % (args.port)

    # Respond to requests until process is killed
    httpd.serve_forever()
