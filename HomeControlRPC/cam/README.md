Cam RPC App
===========

Django app that implements the WebCam RPC functionality of my home-control framework.

The API is based completely on HTTP GET requests,
with commands mapped to URI's and parameters passed into commands as URL query strings.


App Description
---------------

This app allows taking webcam snapshots remotely via the snapshot API. 


Cam RPC App API Documentation
-----------------------------

### `snapshot/` URL

The snapshot URL is used to take a webcam snapshot.

There are no parameters for this command.

If successful, the command returns the snapshot taken in the HTTP Response (use the content-type to determine the image type).

If the snapshot failed, the response will be a JSON string with an error message.


App Configuration
-----------------

The app uses the Django DB to store configuration,
so the configuration is managed via Django admin interface.

For taking snapshots, the app will iterate over available `WebCam` records in the app table (ordered by the priority defined for each record),
and try to take a snapshot with the settings defined by the record,
until a successful snapshot is taken, which is then returned.

The settings:

* `name`: A name for this record. For convenience.
* `priority`: A positive integer representing the record priority. Lower numbers are used before higher numbers.
* `webcam_source`: A string denoting the webcam source to use for snapshots.
  * In Windows, this should be the device number passed to `VideoCapture.Device` (converted to int of course).
  * In Linux, this should be the path of the `gst-launch` executable.
  * In all platforms, if the field is a path to an existing image file, the file will be returned instead of a live snapshot. If the field is a path to an existing directory, a random file from the directory will be selected (and returned if it's an image).
  * Default value is "0" in Windows (for the first webcam device), and "gst-launch-0.10" is Linux.
* `snapshot_file`: A full path to the file to hold the temporary snapshot taken. Leave blank (default) to use a randomly generated temporary file. The web server will need write access to this path.


App Requirements
----------------

- Windows: [VideoCapture](http://videocapture.sourceforge.net/)
- Linux: [GStreamer](http://gstreamer.freedesktop.org/) gst-launch program.
