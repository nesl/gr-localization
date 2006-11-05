from gnuradio import gr, eng_notation
from gnuradio import usrp
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import math, struct, time, sys

def pick_subdevice(u):
    """
    The user didn't specify a subdevice on the command line.
    If there's a daughterboard on A, select A.
    If there's a daughterboard on B, select B.
    Otherwise, select A.
    """
    if u.db[0][0].dbid() >= 0:       # dbid is < 0 if there's no d'board or a problem
        return (0, 0)
    if u.db[1][0].dbid() >= 0:
        return (1, 0)
    return (0, 0)

class rx_graph (gr.flow_graph):
    def __init__(self):
        gr.flow_graph.__init__(self)

        parser = OptionParser (option_class=eng_option)
        parser.add_option("-R", "--rx-subdev-spec", type="subdev", default='B',
                          help="select USRP Rx side A or B (default=first one with a daughterboard)")
        parser.add_option ("-c", "--cordic-freq", type="eng_float", default=434845200,
                           help="set rx cordic frequency to FREQ", metavar="FREQ")
        parser.add_option ("-g", "--gain", type="eng_float", default=0,
                           help="set Rx PGA gain in dB [0,20]")
        
        (options, args) = parser.parse_args ()
        print "cordic_freq = %s" % (eng_notation.num_to_str (options.cordic_freq))
        

        # ----------------------------------------------------------------

        self.freq = 1000
        self.samples_per_symbol = 256
        self.usrp_decim = int (64e6 / self.samples_per_symbol / self.freq)
        self.fs = self.freq * self.samples_per_symbol

        print "freq = ", eng_notation.num_to_str(self.freq)
        print "samples_per_symbol = ", self.samples_per_symbol
        print "usrp_decim = ", self.usrp_decim
        print "fs = ", eng_notation.num_to_str(self.fs)

        u = usrp.source_s (0, self.usrp_decim)
        if options.rx_subdev_spec is None:
            options.rx_subdev_spec = pick_subdevice(u)
        u.set_mux(usrp.determine_rx_mux_value(u, options.rx_subdev_spec))

        subdev = usrp.selected_subdev(u, options.rx_subdev_spec)
        print "Using RX d'board %s" % (subdev.side_and_name(),)

        u.tune(0, subdev, options.cordic_freq)
        u.set_pga(0, options.gain)
        u.set_pga(1, options.gain)

        self.u = u

        self.filesink = gr.file_sink(gr.sizeof_float, 'rx_sin.dat')
        self.stof = gr.short_to_float()

        filter_coeffs = gr.firdes.low_pass (1.0,                # gain
                                          self.fs,                # sampling rate
                                          self.freq,              # low pass cutoff freq
                                          0.1*self.freq,                # width of trans. band
                                          gr.firdes.WIN_HANN) # filter type 
        
        self.lowpass = gr.fir_filter_fff(1, filter_coeffs)
        self.connect(self.u, self.stof, self.lowpass, self.filesink)

def main ():

    fg = rx_graph()
    fg.start()

    fg.wait()
    
if __name__ == '__main__':
    # insert this in your test code...
    #import os
    #print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
