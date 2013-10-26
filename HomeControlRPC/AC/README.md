A/C RPC App
===========

Django app that implements the A/C RPC functionality of my home-control framework.

The API is based completely on HTTP GET requests,
with commands mapped to URI's and parameters passed into commands as URL query strings.

Results of commands are returned as JSON objects over HTTP responses.

App Description
---------------

For detailed description, refer to [my blog post on my A/C Control project](http://itamaro.com/2013/10/04/ac-control-project-bringing-it-together/).

This app implements the A/C RPC part of the project, by receiving commands from the web front-end,
using a connected Arduino to send out the IR signals,
and using a microphone to listen for beeps from the A/C as feedback. 


A/C RPC App API Documentation
-----------------------------

### `command/` URL

The command URL is used to trigger IR signals based on the parameters passed to the command (as query string):

* `mode`: A/C mode to set (mode number enum)
* `fan`:  A/C fan speed to set (fan speeds enum)
* `temp`: A/C temperature to set (as a number)
* `pwr`:  Whether the command toggles the A/C power state or not (power enum)

This command returns a string to denote the command result:

* `Success`: Command was sent successfully, and a beep was detected as feedback.
* `Beep Timeout`: Command was sent successfully, but no beep was detected as feedback (either the A/C did not receive the command, or the beep was missed - can't tell which).
* `Missing Parameter`: One or more of the parameters was missing (they are all required).
* `Serial Error`: There was an error accessing the Arduino over the serial interface.
* `Unsupported Parameter Value [...]`: A supplied parameter had a value that is not supported.


App Configuration
-----------------

The app uses the Django DB to store configuration,
so the configuration is managed via Django admin interface.

For sending A/C commands, the app will iterate over available `AcControl` records in the app table (ordered by the priority defined for each record),
and try to send the IR signal with the settings defined by the record,
until a "Success" or "Beep Timeout" result is received.

The settings:

* `name`: A name for this record. For convenience.
* `serial_port`: A string defining the serial interface to use (e.g. `/dev/tty*` on Linux, or `COM#` on Windows). Supply special string `MOCK-SERIAL` to mock behavior of serial interface, as if an Arduino is connected.
* `priority`: A positive integer representing the record priority. Lower numbers are used before higher numbers.
* `beep_timeout`: Timeout (float in seconds) to wait for a beep after sending IR signal (default: 1.5 sec)
* `listen_delay`: The time (float in seconds) to wait between starting listening on the microphone and sending the IR signal (default: 0.2 sec)
* `debug_rec_file`: A full path to a debug recording file (that must be write-accessible to the Django process), that will be used to store the beep-detection recording, if not blank (default: blank).

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *   


Stand Alone Programs
====================

mic.py - Audio processing for Beep detection
--------------------------------------------

The main objective of this module is to supply the `MicAnalyzer` class as an API
for the A/C RPC app to receive beep-detection functionality.

Design considerations, examples, and some implementation details may be found in
[my blog post](http://itamaro.com/2013/09/24/ac-control-project-using-beeps-for-feedback).

### MicAnalyzer API Documentation
For detailed method-arguments and default values documentation - [read in the code](mic.py).
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


### Dependencies

- For live audio recording, the module depends on [PyAlsaAudio library](http://pyalsaaudio.sourceforge.net/pyalsaaudio.html) for Linux.
- For signal energy graphing, the module depends on [matplotlib library](http://matplotlib.org/) (version >= 3.0).
