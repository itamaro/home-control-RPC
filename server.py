import os
import argparse
from wsgiref.simple_server import make_server
from webcam import WebCam
from arduino import AcControl

parser = argparse.ArgumentParser(description=
                                 'Home Control RPC auxiliary server.')
parser.add_argument('--host', default='',
                    help='Host name for WSGI server')
parser.add_argument('--port', type=int, default=8001,
                    help='Port for WSGI server')
parser.add_argument('--serial', default='/dev/ttyACM0',
                    help='Serial port where Arduino is connected')
parser.add_argument('--mock_serial', action='store_true',
                    help='Enable serial port mocking')
parser.add_argument('--debug', action='store_true',
                    help='Enable debug server')
args = parser.parse_args()

cam = WebCam()
cam.saveSnapshot()

ac_control = AcControl(args.serial, args.mock_serial)

def application(
        # environ points to a dictionary containing CGI like env-variables
        # which is filled by the server for each received request
        environ,
        # start_response is a callback function supplied by the server
        # which will be used to send the HTTP status and headers to the server
        start_response):
    
    pathinfo = environ['PATH_INFO']
    if '/webcam.png' == pathinfo:
        status = '200 OK'
        response_headers = [('Content-Type', 'image/png'),]
        start_response(status, response_headers)
        return open(cam.saveSnapshot(), 'rb').read()
    elif '/ac-command' == pathinfo:
        status = '200 OK'
        response_body = ac_control.sendCommand()
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
