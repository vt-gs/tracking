#!/usr/bin/env python
from optparse import OptionParser
from tracker_module import *
from curses_display import *
from predict import *
import sys

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    pred_ip_h    = "IP address of Predict Server, Default: 127.0.0.1"
    pred_port_h  = "Port Number of Predict Server, Default: 1210"
    track_ip_h   = "IP address of tracker, Default: 192.168.20.3"
    track_port_h = "TCP port number of tracker, Default: 196"
    sat_id_h     = "Satellite ID, NORAD ID # or Sat Name"
    interval_h   = "Predict Update Interval, default = 1.0 seconds"
    parser.add_option("--predict-ip"  , dest = "pred_ip"   , action = "store", type = "string", default = "127.0.0.1", help = pred_ip_h)
    parser.add_option("--predict-port", dest = "pred_port" , action = "store", type = "int"   , default = "1210"     , help = pred_port_h)
    parser.add_option("--tracker-ip"  , dest = "track_ip"  , action = "store", type = "string", default = "192.168.20.3", help = track_ip_h)
    parser.add_option("--tracker-port", dest = "track_port", action = "store", type = "int"   , default = "196"      , help = track_port_h)
    parser.add_option("--sat-id"      , dest = "sat_id"    , action = "store", type = "string", default = ""         , help = sat_id_h)
    parser.add_option("--interval"    , dest = "interval"  , action = "store", type = "float" , default = "1.0"      , help = interval_h)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    if options.sat_id == "":
        print "Must Enter a Satellite Name using the --sat-id flag"
        print "Terminating..."
        sys.exit()

    pt = Predict_Thread(options)
    tt = Tracker_Thread(options)
    dt = Display_Thread(options, tt, pt)
    pt.daemon = True
    tt.daemon = True
    dt.daemon = True
    pt.start()
    tt.start()
    dt.run()
    sys.exit()

    #stop_flag = False
    #while not stop_flag:
    #    os.system("clear")
    #    command = raw_input("Enter WAAA EEE or (q)uit: ")
    #    if command == 'q':
    #        stop_flag = True
    #        print "terminating, please wait..."
    #    else:
    #        tt.Write_Raw_Message(command)
        
    #dt.run()
    #print "terminating, please wait..."
    #tt.stop()
    #dt.stop()
    #pt.join()

