from gnuradio import gr, eng_notation, optfir
from gnuradio import usrp
from gnuradio import audio
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import math
import struct, time

class transmit_path(gr.flow_graph):
    def __init__(self):
        gr.flow_graph.__init__(self)

        parser = OptionParser (option_class=eng_option)
        parser.add_option("-T", "--tx-subdev-spec", type="subdev", default=None,
                          help="select USRP Tx side A or B (default=first one with a daughterboard)")
        parser.add_option ("-c", "--cordic-freq", type="eng_float", default=434845200,
                           help="set Tx cordic frequency to FREQ", metavar="FREQ")

        (options, args) = parser.parse_args ()
        print "cordic_freq = %s" % (eng_notation.num_to_str (options.cordic_freq))

        self.normal_gain = 8000
        self.u = usrp.sink_s()
        dac_rate = self.u.dac_rate();
        self._freq = 1000
        self._spb = 256
        self._interp = int(128e6 / self._spb / self._freq)
        self.fs = 128e6 / self._interp
        print "Interpolation:", self._interp
        
        self.u.set_interp_rate(self._interp)

        # determine the daughterboard subdevice we're using
        if options.tx_subdev_spec is None:
            options.tx_subdev_spec = usrp.pick_tx_subdevice(self.u)
        self.u.set_mux(usrp.determine_tx_mux_value(self.u, options.tx_subdev_spec))
        self.subdev = usrp.selected_subdev(self.u, options.tx_subdev_spec)
        print "Using TX d'board %s" % (self.subdev.side_and_name(),)

        self.u.tune(self.subdev._which, self.subdev, options.cordic_freq)

        self.sin = gr.sig_source_f(self.fs, gr.GR_SIN_WAVE, self._freq, 1, 0)
        self.gain = gr.multiply_const_ff (self.normal_gain)
        self.ftos = gr.float_to_short()
        
        self.filesink = gr.file_sink(gr.sizeof_float, 'sin.dat')
        
        self.connect(self.sin, self.gain)
        self.connect(self.gain, self.ftos, self.u)
        self.connect(self.gain, self.filesink)
        
        self.set_gain(self.subdev.gain_range()[1])  # set max Tx gain
        self.set_auto_tr(True)                      # enable Auto Transmit/Receive switching

    def set_gain(self, gain):
        self.gain = gain
        self.subdev.set_gain(gain)

    def set_auto_tr(self, enable):
        return self.subdev.set_auto_tr(enable)

def main ():
    tx = transmit_path()

    tx.start()

    tx.wait()


if __name__ == '__main__':
    # insert this in your test code...
    #import os
    #print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
