#!/usr/bin/env python
from optparse import OptionParser
from tracker_module import *
from curses_display import *

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of tracker, Default: 127.0.0.1"
    p_help = "TCP port number of tracker, Default: 196"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.20.3", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "196"      , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    tt = Tracker_Thread(options)
    dt = Display_Thread(options, tt)
    tt.daemon = True
    dt.daemon = True
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

