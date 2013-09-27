HomeControl RPC Server and Modules
==================================

Python modules that implement RPC services for the Home Control system.

mic.py - Audio processing for Beep detection
--------------------------------------------

The main objective of this module is to supply the `MicAnalyzer` class as an API
for the RPC server to receive beep-detection functionality.

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


### Dependencies

- For live audio recording, the module depends on [PyAlsaAudio library](http://pyalsaaudio.sourceforge.net/pyalsaaudio.html) for Linux.
- For signal energy graphing, the module depends on [matplotlib library](http://matplotlib.org/) (version >= 3.0).
