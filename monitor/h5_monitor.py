import logging, argparse
import sys, pickle
import SocketServer, socket
from collections import defaultdict
import pandas as pd
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.multiprocess as mp

class MonitorHandler(SocketServer.BaseRequestHandler):
   
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('MonitorHandler')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
    
        self.logger.debug("Starting handler.")

        data = pickle.loads(self.request[0])  
        self.logger.debug('reading data as: %s',data)

        print data["event_id"], data["address"]

        self.logger.debug('Calculating current cache size')
        if self.server.cache.keys():
            cache_keys = self.server.cache.keys()
            first_key = cache_keys[0]
            size = len(self.server.cache[first_key])

        else:
            size = 0

        self.logger.debug("Cache size: %s", size)

        if size >= self.server.max_cache_size:
            self.logger.debug("Writing to h5 store and flushing cache.")
            df = pd.DataFrame(self.server.cache)
            self.server.h5_store.append(self.server.h5_key, df)
            self.server.h5_store.flush() 
            self.server.cache.clear()

        self.logger.debug('Appending to cache')
        for key, item in data.iteritems():
            self.server.cache[key].append(item)


        # here we compute the stuff we need to update the plots
        # in particular computing a histogram every time is very expensive
        
        if self.server.h5_key in self.server.h5_store:

            self.logger.debug("Building data frame of the past.")
            df = self.server.h5_store[self.server.h5_key]
            df = df.set_index("timestamp")

            end_time_window = df.index.max()
            # only consider the data which falls into the time window
            start_time_window = end_time_window - pd.DateOffset(seconds=self.server.time_window)
            df_slice = df.ix[start_time_window:]
            df_slice.sort_index()

            self.logger.debug("Calculating neuron spikes.")
            df_slice['timedelta_in_seconds'] = df_slice['timedelta'] / np.timedelta64(1, 's')

            self.logger.debug("Updating plot.")
            self.server.spikes_curve.setData( x=df_slice["timedelta_in_seconds"].tolist(), y=df_slice["address"].tolist(), _callSync='off')
            
            self.logger.debug("Calculating neuron firing rates.")
            # if you need more sophisticated methods for computing the firing rate, they need to go here
            df_slice_hist = df_slice["address"].value_counts()
            df_slice_hist = df_slice_hist/self.server.time_window

            self.logger.debug("Updating plot.")
            self.server.spikes_rate_curve.setData( x=df_slice_hist.index.tolist(), y=df_slice_hist.tolist(), _callSync='off')

            self.logger.debug("Calculating histogram of neuron firing rates.")
            y,x = np.histogram(df_slice_hist)
            self.server.spikes_histogram_curve.setData(x,y)
        
        self.logger.debug("Finishing handler.")

        return

class MonitorServer(SocketServer.UDPServer):
    
    def __init__(self, server_address, handler_class, max_cache_size, h5_key, h5_path, time_window ):
        self.logger = logging.getLogger('MonitorServer')
        self.logger.debug('__init__')
        SocketServer.UDPServer.__init__(self, server_address, handler_class)

        # stuff for data handling
        pd.options.mode.chained_assignment = None
        self.cache = defaultdict(list)
        self.max_cache_size = max_cache_size
        self.h5_key = h5_key
        self.h5_path = h5_path
        self.logger.debug("Opening h5 store as: %s", h5_path)
        self.h5_store = pd.HDFStore(h5_path,'w', libver='latest')
        self.time_window = time_window

        # stuff for plotting
        pg.mkQApp()
        self.proc = mp.QtProcess()
        self.rpg = self.proc._import('pyqtgraph')
        
        self.plotwin = self.rpg.GraphicsWindow(title="Monitor")
        self.plotwin.resize(1000,600)
        self.plotwin.setWindowTitle('Activity Monitor')

        self.p1 = self.plotwin.addPlot(title="Neuron spikes vs. time")
        self.p1.setLabel('left', 'Neuron Id')
        self.p1.setLabel('bottom', 'Time [s]')
        self.spikes_curve = self.p1.plot(pen=None, symbol = "+")
        self.plotwin.nextRow()

        self.p2 = self.plotwin.addPlot(title="Firing rates")
        self.p2.setLabel('left', 'Firing rate [events/period]')
        self.p2.setLabel('bottom', 'Neuron Id')
        self.spikes_rate_curve = self.p2.plot(pen=None, symbol = "+")

        self.plotwin.nextRow()
        self.p3 = self.plotwin.addPlot(title="Histogram of firing rates")
        self.p3.setLabel('left', 'Firing events')
        self.p3.setLabel('bottom', 'Firing rate [events/period]')
        self.spikes_histogram_curve = self.p3.plot(stepMode=True, fillLevel=0, brush=(0,0,255,150))

        return

    def serve_forever(self):
        self.logger.debug('waiting for request')
        self.logger.info('Handling requests, press <Ctrl-C> to quit')
        
        try:
            while True:
                self.handle_request()

        except KeyboardInterrupt: 
            self.logger.debug('Keyboard interrupt. Server is closing.')
            self.server_close()

        return

    def server_close(self):
        self.logger.debug('server_close')
        self.logger.info('Flushing and closing h5 store at: %s', self.h5_path)
        self.h5_store.append(self.h5_key, pd.DataFrame(self.cache))
        self.h5_store.flush()
        self.h5_store.close()
        return SocketServer.UDPServer.server_close(self)

if __name__ == '__main__':

    # get the current timestamp and turn it into a string with second precision
    now = pd.Timestamp(np.datetime64(datetime.datetime.now())).strftime("%Y-%m-%d_%H:%M:%S")
    # now = ""

    # setup parser for command line arguments
    parser = argparse.ArgumentParser(description='Real-time h5 network data monitor', epilog='... now this is how you log your data.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--sender_ip', metavar="", help='IP address of sending machine', type=str, default = socket.gethostname() )
    parser.add_argument('-p','--port', metavar="", help='port to listen to on sending machine', type=int, default = 60000)
    parser.add_argument('-f', '--h5_file', metavar="", help="file for h5 storage opened as", type=str, default = "h5_store_" + now +".h5"   )
    parser.add_argument('-t','--time_window', metavar="", help='time window for plotting in seconds. ', type=int, default = 10)
    parser.add_argument('-k', '--h5_key', metavar="", help="h5 storage key", type=str, default = "address")
    parser.add_argument('-c','--cache_size', metavar="", help='wait for this number of data entries to be recieved before flushing cache to h5 store', type=int, default = 1)
    parser.add_argument('-l', '--log_file', metavar="", help="file for logs opened as", type=str, default = "h5_store_" + now +".log"   )
    args = parser.parse_args()


    # setup logging to file
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s: %(name)s: -- %(levelname)s -- %(message)s',
                        filename=args.log_file,
                        filemode='w')


    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)s: -- %(levelname)s -- %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info('Starting real-time network data monitoring ...')
    logging.info('Listen to ip address: %s', args.sender_ip )
    logging.info('Listen to port: %s', args.port )
    logging.info('Server cache size: %s', args.cache_size)
    logging.info('Arriving data is logged to h5 store: %s', args.h5_file)
    logging.info('Selected h5 key: %s', args.h5_key)
    logging.info('Log files is specified as: %s', args.log_file)
    logging.info('Time window for plotting data is: %s', args.time_window)

    logging.info('Configuring server ...')
    logging.info('Configuring monitor ...')
    address = (args.sender_ip, args.port)
    server = MonitorServer(address, MonitorHandler, args.cache_size, args.h5_key, args.h5_file, args.time_window)
        
    logging.info('All systems go.')
    logging.info('Listening for incoming data ...')
    
    try:
        server.serve_forever()

    except Exception as e:
        logging.exception('Exception in server')
        sys.exit(1)

