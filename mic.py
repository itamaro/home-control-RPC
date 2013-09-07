import threading
import struct
import sys
from Queue import Queue, Empty
import numpy

# The MicListenerThread will listen on a live-microphone (or simulate it using
# a pre-recorded audio file), and push recorded sample onto a queue for
# processing by a worker thread (that owns the queue).
MODE_MIC = 1
MODE_MOCK_FILE = 2
class MicListenerThread(threading.Thread):
    def __init__(self, sample_buffer, mode=MODE_MIC, mock_file=None,
                 rec_time=5.0, rate=44100, name='mic-listening-thread'):
        threading.Thread.__init__(self, name=name)
        self.sample_buffer = sample_buffer
        self.mode = mode
        self.mock_file = mock_file
        self.rec_time = rec_time
        self.rate = rate
        self.period_size = 160
        self._stop = threading.Event()
    
    # ask the thread to stop listening and terminate, without waiting for
    # timeout to elapse.
    def stop(self):
        self._stop.set()
    
    def stopped(self):
        self._stop.isSet()
        
    def run(self):
        if self.rec_time:
            iter = int(self.rec_time * self.rate / self.period_size)
        else:
            iter = float('+inf')
        if MODE_MIC == self.mode:
            import alsaaudio
            # Open the device in capture mode.
            inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)

            # Set attributes: Mono, 44100 Hz, 16 bit little endian samples
            inp.setchannels(1)
            inp.setrate(self.rate)
            inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

            # The period size sets the internal number of frames per period.
            # Reads from the device will return this many frames.
            # Each frame being 2 bytes long.
            inp.setperiodsize(self.period_size)
            
            while iter > 0 and not self.stopped():
                iter -= 1
                # Read data from device
                length, data = inp.read()
                if length:
                    self.sample_buffer.put(data)
                    
        elif MODE_MOCK_FILE == self.mode:
            f = self.mock_file
            if type(f) is str:
                f = open(f, 'rb')
            while iter > 0 and not self.stopped():
                data = f.read(2 * self.period_size)
                while data and iter > 0 and not self.stopped():
                    iter -= 1
                    self.sample_buffer.put(data)
                    data = f.read(2 * self.period_size)
                f.seek(0)
            f.close()

THRESHOLD_FILE_NAME = 'beep-thresh'
def load_beep_thresh():
    try:
        with open(THRESHOLD_FILE_NAME, 'r') as f:
            return float(f.readline())
    except IOError, ex:
        raise IOError('Threshold file missing. Please run `calibrate`')

class MicAnalyzer(object):
    
    def __init__(self,
            rate=44100,             # Sample rate of raw signal (Hz)
            time_window=0.500,      # Time window for energy extraction (sec)
            time_step=0.100,        # Time step for energy extraction (sec)
            center_freq=4100,       # Center frequency of beep (Hz)
            freq_width=100,         # Width of frequency band to analyze (Hz)
            ):
        self.sample_buffer = Queue()
        assert(rate > 0)
        assert(time_window > 0)
        assert(time_step > 0)
        assert(freq_width > 0)
        self.rate = rate
        self.time_window = time_window
        self.time_step = time_step
        self.min_freq, self.max_freq = center_freq - freq_width / 2,    \
                                       center_freq + freq_width / 2
        self.queue_timeout = 0.050 # time to wait on queue for samples (sec)
        self.bytes_per_sample = 2
        self.listener = None
    
    # calculate the total energy if a given signal in a given frequency-range
    def get_energy_in_freq_range(self, signal):
        ts = 1.0 / self.rate
        fourier = numpy.fft.fft(signal)
        freq = numpy.fft.fftfreq(len(signal), d=ts)
        freq_range = numpy.where(numpy.logical_and(freq>self.min_freq,
                                                   freq<self.max_freq))
        if 0 == freq_range[0].size:
            # no frequencies in the range - no energy
            return 0.0
        energy = 0.0
        for ff in freq_range[0]:
            energy += abs(fourier[ff])
        # doubling the result to account for symmetric negative frequencies
        return 2 * energy / float(freq_range[0].size)
    
    # This generator yields (time-stamp, energy-value) tuples from a signal
    # that is being recorded by a listener thread.
    # Every `time_step` seconds the generator will yield a tuple
    # with the current time, and the total energy of the signal in the
    # configured frequency-range in the last `time_window` seconds.
    def energy_generator(self):
        window_size = int(self.rate * self.time_window)
        step_size = int(self.rate * self.time_step)
        signal = list()
        pos = 0
        try:
            while True:
                samples = self.sample_buffer.get(block=True,
                                                 timeout=self.queue_timeout)
                sample_count = len(samples) / self.bytes_per_sample
                frmt = '<%dh' % (sample_count)
                signal.extend(struct.unpack(frmt, samples))
                self.sample_buffer.task_done()
                while len(signal) - pos >= window_size:
                    # enough new samples accumulated for energy extraction
                    energy = self.get_energy_in_freq_range(
                                            signal[pos:pos+window_size])
                    yield float(pos + window_size) / self.rate, energy
                    pos += step_size
        except Empty, ex:
            pass
    
    # Activate the listening thread.
    def start_listen(self, rec_time=5.0, rec_file=None):
        if rec_file:
            self.listener = MicListenerThread(self.sample_buffer,
                                              MODE_MOCK_FILE,
                                              rec_time=rec_time,
                                              mock_file=rec_file)
        else:
            self.listener = MicListenerThread(self.sample_buffer,
                                              MODE_MIC,
                                              rec_time=rec_time)
        self.listener.start()
    
    # Listens up to `timeout` seconds.
    # returns `True` if beep is detected during listening period,
    # otherwise- returns `False`.
    def is_beep(self, timeout=3.0, rec_file=None):
        beep_thresh = load_beep_thresh()
        self.start_listen(timeout, rec_file)
        for ts, energy in self.energy_generator():
            if energy >= beep_thresh:
                # tell the thread to stop listening (even before timeout)
                # and wait for it the terminate before returning
                self.listener.stop()
                self.listener.join()
                return True
        return False

# Calibrate the beep-threshold value,
# using either live-microphone or pre-recorded raw files.
def calibrate(args):
    print '~~ Welcome to the beep-detection calibrator tool! ~~'
    if args.noise_file:
        print 'Detected noise-file. Processing...'
    else:
        print 'Please record a few seconds of background noise (5sec).'
        print 'Place the microphone in its final location, and keep quiet.'
        raw_input('When ready, hit Enter')
    analyzer = MicAnalyzer(args.rate, args.time_window, args.time_step,
                           args.beep_freq, args.freq_band)
    analyzer.start_listen(5.0, args.noise_file)
    nemin = float('+inf')
    nemax = 0
    for ts, energy in analyzer.energy_generator():
        nemin = energy if energy < nemin else nemin
        nemax = energy if energy > nemax else nemax
        sys.stdout.write('.')
    noise_thresh = 2 * nemax
    print '\t', nemin, nemax
    print 'Noise-based threshold set to', noise_thresh
    if args.beep_file:
        print 'Detected beeps-file. Processing...'
    else:
        print 'Please record a few seconds of with at least one beep.'
        print 'Place the microphone in its final location, '     \
              'and make beeps during the following 5 seconds.'
        raw_input('When ready, hit Enter')
    analyzer = MicAnalyzer(args.rate, args.time_window, args.time_step,
                           args.beep_freq, args.freq_band)
    analyzer.start_listen(5.0, args.beep_file)
    beeps = list()
    inbeep = False
    for ts, energy in analyzer.energy_generator():
        if energy < noise_thresh:
            # below noise-based threshold - assume it's noise...
            inbeep = False
            sys.stdout.write('.')
        else:
            # Above noise-based threshold -
            #   gather signal stats for refined threshold.
            if not inbeep:
                # starting a new beep - add another energies list
                beeps.append(list())
                inbeep = True
            beeps[-1].append(energy)
            sys.stdout.write('*')
    print ''
    if beeps:
        print 'Detected %d beeps in the signal.' % (len(beeps))
        if args.beep_count:
            detect_success = args.beep_count == len(beeps)
        else:
            detect_success = 'Y' == str.upper(raw_input('Does this match ' \
                      'the number of beeps you heard? (''Y'' or ''N'') ')[0])
        if detect_success:
            # Go over the beeps, calculate the mean energy level of each one,
            # and set the final threshold to be the average of the weakest one
            beep_thresh = int(min([numpy.mean(beep) for beep in beeps]))
            print 'Calibration completed successfully!'
            with open(THRESHOLD_FILE_NAME, 'w') as f:
                f.write('%d\n' % (beep_thresh))
            print 'Final beep threshold set to', beep_thresh
        else:
            print 'Failed calibration. Please try again'
    else:
        # None of the measurements was above the noise-based threshold...
        print 'Could not detect beeps - please try again'

# Produce a nice (XKCD-style!) energy graph of a raw audio signal,
# either from a live microphone, or from a pre-recorded audio file.
def graph(args):
    energies = list()
    timestamps = list()
    analyzer = MicAnalyzer(args.rate, args.time_window, args.time_step,
                           args.beep_freq, args.freq_band)
    analyzer.start_listen(args.rec_time, args.rec_file)
    for ts, energy in analyzer.energy_generator():
        timestamps.append(ts)
        energies.append(energy)
    import matplotlib.pyplot as plt
    plt.xkcd()
    plt.plot(timestamps, energies, 'blue', alpha=0.4)
    plt.title('Signal Energy (time-windowed)')
    plt.xlabel('time [sec]')
    plt.ylabel('signal energy [wtf]')
    plt.show()

# Look for beeps in a recording,
# and print the time ranges where beeps were detected
def detect(args):
    beep_thresh = load_beep_thresh()
    analyzer = MicAnalyzer(args.rate, args.time_window, args.time_step,
                           args.beep_freq, args.freq_band)
    analyzer.start_listen(args.rec_time, args.rec_file)
    beeps = list()
    inbeep = False
    for ts, energy in analyzer.energy_generator():
        if energy >= beep_thresh:
            sys.stdout.write('*')
            if not inbeep:
                # starting a new beep sequence
                beeps.append((ts,))
                inbeep = True
        else:
            sys.stdout.write('.')
            if inbeep:
                # ending a beep sequence
                beeps[-1] = beeps[-1] + (ts,)
                inbeep = False
    print ''
    print 'Detected %d beeps:' % (len(beeps))
    for tb, te in beeps:
        print 'Beep from %.2fs through %.2fs' % (tb, te)

# Return as soon as a beep is detected
def isbeep(args):
    analyzer = MicAnalyzer(args.rate, args.time_window, args.time_step,
                           args.beep_freq, args.freq_band)
    if analyzer.is_beep(timeout=args.rec_time, rec_file=args.rec_file):
        print 'Beep detected'
    else:
        print 'Beep not detected'

if '__main__' == __name__:
    import argparse
    import os
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    parser = argparse.ArgumentParser(description=
                                     'Beep module utilities.')
    parser.add_argument('-r', '--rate', type=int, default=44100,
                        help='The raw recording sampling rate (Hz)')
    parser.add_argument('-w', '--time-window', type=float, default=0.500,
                        help='Time window for energy extraction (sec)')
    parser.add_argument('-s', '--time-step', type=float, default=0.100,
                        help='Time step for energy extraction (sec)')
    parser.add_argument('-fb', '--beep-freq', type=int, default=4100,
                        help='Center frequency of beep (Hz)')
    parser.add_argument('-fw', '--freq-band', type=int, default=100,
                        help='Width of frequency band to analyze (Hz)')
    parser.add_argument('-t', '--rec-time', type=float, default=5.0,
                        help='Recording length (sec)')
    subparsers = parser.add_subparsers()
    # Add file energy graphing subcommand
    parser_graph = subparsers.add_parser('graph',
                              help='Graph the energy of raw audio')
    parser_graph.add_argument('-fr', '--rec-file',
                              type=argparse.FileType('rb'),
                              help='A raw recording file')
    parser_graph.set_defaults(func=graph)
    # Add beep-detection test subcommand
    parser_detect = subparsers.add_parser('detect',
                               help='Test beep-detecion on raw audio')
    parser_detect.add_argument('-fr', '--rec-file',
                               type=argparse.FileType('rb'),
                               help='A raw recording file')
    parser_detect.set_defaults(func=detect)
    # Add beep-detection test subcommand
    parser_isbeep = subparsers.add_parser('isbeep',
                               help='Test is-beep-detecion on raw audio')
    parser_isbeep.add_argument('-fr', '--rec-file',
                               type=argparse.FileType('rb'),
                               help='A raw recording file')
    parser_isbeep.set_defaults(func=isbeep)
    # Add noise/beep levels calibration subcommand
    parser_calib = subparsers.add_parser('calibrate',
                              help='Calibrate the beep detector')
    parser_calib.add_argument('-nf', '--noise-file',
                              type=argparse.FileType('rb'),
                              help='A raw recording file with just noise')
    parser_calib.add_argument('-bf', '--beep-file',
                              type=argparse.FileType('rb'),
                              help='A raw recording file with beep(s)')
    parser_calib.add_argument('-bc', '--beep-count', type=int,
                              help='Number of distinct beeps in the signal')
    parser_calib.set_defaults(func=calibrate)
    
    args = parser.parse_args()
    args.func(args)
