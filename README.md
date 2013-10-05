HomeControl RPC Server and Modules
==================================

Python modules that implement RPC services for my [Home Control system](https://github.com/itamaro/home-control-web).

Also see [my blog post](http://itamaro.com/2013/10/04/ac-control-project-bringing-it-together/).

The RPC server should be installed on the devices that will be responsible for interacting with the controlled systems
(e.g. a Linux laptop, raspberry-pi, or whatever, that connects to an Arduino / webcam / microphone),
and the [home-control web-app](https://github.com/itamaro/home-control-web) needs to be configured to communicate with the RPC server.


Installation
------------

Requirements:

1. Python (tested with 2.7)
2. For Arduino interaction:
   1. [PySerial library](http://pyserial.sourceforge.net/) & root privileges!
   2. [PyAlsaAudio library](http://pyalsaaudio.sourceforge.net/pyalsaaudio.html) for live audio recording on Linux (no support for audio recording on Windows).
   3. Optional: [matplotlib library](http://matplotlib.org/) (version >= 3.0) for signal energy graphing.
3. For webcam interaction:
   1. On Linux: [GStreamer](http://gstreamer.freedesktop.org/)
   2. On Windows: [VideoCapture](http://videocapture.sourceforge.net/)

Get and configure the RPC server:

1. Clone the repository to the machine / device that will run it.
2. Create a `local_settings.py` file in [HomeControlRPC](HomeControlRPC/) to override settings from the [generic settings](HomeControlRPC/settings.py).

A sample configuration for a set up with Arduino for A/C control, connected over USB to a Ubuntu Linux laptop, listening in port 8001:

```python
# Modules selection section
ARDUINO_ENABLED =   True
CAM_ENABLED =       False

# WSGI HTTP server parameters
WsgiHost = ''
WsgiPort = 8001

# Serial port device ID where the Arduino is connected
# ('COM#' on Windows, some '/dev/tty*' on Linux)
# set to 'MOCK-SERIAL' in order to use a mock serial port instead of a real one
SerialPortID = '/dev/ttyACM0'
```

(see the [generic settings file](HomeControlRPC/settings.py) for all overridable parameters and their default values)

If used for A/C control with beep-detection-based feedback - place the microphone in its final location and run the beep calibration wizard:

1. `cd /path/to/home-control-RPC/HomeControlRPC`
2. `python mic.py calibrate` (note: run as a user that has write access to the directory. [see below](#stand-alone-program-commands-and-parameters) for more details on mic module commands)

Start the server:

1. `cd /path/to/home-control-RPC/HomeControlRPC`
2. `sudo python server.py` (note: required to run as root in order to open serial channel)

TODO: Add details regarding setting up as a service instead of manual execution.


mic.py - Audio processing for Beep detection
--------------------------------------------

The main objective of this module is to supply the `MicAnalyzer` class as an API
for the RPC server for beep-detection functionality.

Design considerations, examples, and some implementation details may be found in
[my blog post](http://itamaro.com/2013/09/24/ac-control-project-using-beeps-for-feedback).

### MicAnalyzer API Documentation
For detailed method-arguments and default values documentation - [read in the code](HomeControlRPC/mic.py).
- Object initialization takes various (all optional) parameters regarding audio processing for beep detection (sample rate, expected beep-frequency and band-width, time-windowing parameters).
- `statr_listen(...)` - creates a listening thread that feeds samples for processing by the main thread.
- `energy_generator()` - a generator method yielding (`timestamp`, `energy`) tuples extracted from the processed audio signal.
- `is_beep()` - returns True is a beep is detected during active listening session (and False is the session ends before a beep is detected).

### Stand-alone program commands and parameters
In addition to be used as API, the module also supports execution as stand-alone program with several commands.
- `graph`:       Graphs the energy of a signal over time
- `detect`:      Live beep-detection in audio signal with ..**.. visual feedback
- `isbeep`:      Beep-detection in audio signal with no live feedback, returns on detection
- `calibrate`:   Beep-threshold clibration wizard

Common command-line flags to all commands (all optional):
- `rate`: Audio signal sample rate
- `time-window`: The time-window, in seconds, for which a an energy value is extracted
- `time-step`:   For every time-step (in seconds) starting time-window, an energy value is extracted (calculated over the last time-window seconds)
- `beep-freq`:   The expected central frequency (in Hz) of the beep sound
- `freq-band`:   The estimated band-width around the central frequency to integrate over for energy extraction
- `rec-time`:    The maximal recording length (in seconds) for a single listening session

Common command-line flag (optional) to the graph, detect and isbeep commands:
- `rec-file`:    Pre-recorded PCM file to use instead of live recording

Command-line flags (optional) for the calibrate command:
- `noise-file`:  Pre-recorded PCM file with reference background noise to use instead of noise-recording
- `beep-file`:   Pre-recorded PCM file with beeps to use instead of beep-recording
- `beep-count`:  Number of distinct beeps in pre-recorded beep-file, to use instead of user input

