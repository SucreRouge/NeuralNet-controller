import socket
import SocketServer
import pickle
import pandas as pd
from collections import defaultdict
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as dates
import datetime
import numpy as np

class DataUDPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def read_pickle_stream(self):

        return pickle.loads(self.request[0])

    def send_pickle_stream(self, data):

        # print "Server: Sending answer \t...\t",
        self.request[1].sendto(pickle.dumps(data), self.client_address)
        # print "done."

    def process_row(self, data, hdf5_key, cache, max_cache_size, tail_elements):
        """
        Append row data to the store 'hdf5_key'.

        When the number of items in the cache reaches max_cache_size,
        append the data rows to the HDF5 store and clear the cache.

        """
        def get_cache_size(cache):

            if cache.keys():

                cache_keys = cache.keys()
                first_key = cache_keys[0]

                return len(cache[first_key])

            else:
                return 0

        if get_cache_size(cache) >= max_cache_size:
            self.store_and_clear(cache, hdf5_key)
            self.update_data_tail(hdf5_key, cache , tail_elements)
            self.server.store_tail_changed = True
        else:
            self.server.store_tail_changed = False

        for key, item in data.iteritems():
            cache[key].append(item)

    def store_and_clear(self, data, hdf5_key):
        """
        Convert the cached data dict to a DataFrame and append that to HDF5.
        """
        df = pd.DataFrame(data)
        self.server.hdf_store.append(hdf5_key, df)
        data.clear()

    def update_data_tail(self, hdf5_key, cache, tail_elements):

        if self.server.hdf_store:

            mask = self.server.hdf_store.select_column(hdf5_key,'index')
            df_tail = self.server.hdf_store.select(hdf5_key,where=mask[-tail_elements:].index)        
            self.server.hdf_store_tail = df_tail.reset_index(drop=True)

    def update_tail_plot(self):

        xdata = self.server.hdf_store_tail["timedelta"]
        xdata = [x/np.timedelta64(1, 's') for x in xdata]
        ydata = self.server.hdf_store_tail["address"]

        #Update data (with the new _and_ the old points)
        self.server.lines.set_xdata(xdata)
        self.server.lines.set_ydata(ydata)
        #Need both of these in order to rescale
        self.server.ax.relim()
        self.server.ax.autoscale_view()
        #We need to draw *and* flush
        self.server.fig.canvas.draw()
        self.server.fig.canvas.flush_events()

    def handle(self):
    
        data = self.read_pickle_stream()   
        
        self.process_row(data, hdf5_key = "address", cache = self.server.cache, max_cache_size = self.server.max_cache_size, tail_elements = self.server.tail_elements)
       
        if self.server.hdf_store and self.server.store_tail_changed:

            self.update_tail_plot()

host = '161.122.21.46'
port = 60000

# Create the server, binding it to host and port
server = SocketServer.UDPServer((host,port), DataUDPHandler)
server.cache = defaultdict(list)
# server.cache = {}
server.max_cache_size = 10
server.tail_elements = 50
server.hdf_store = pd.HDFStore("test.h5", "w")
server.hdf_store_tail = None

# Prepare stuff for plotting
server.fig, server.ax = plt.subplots(1, 1)
server.lines, = server.ax.plot([],[], '+')
server.ax.set_autoscaley_on(True)

plt.xticks(rotation=45)
server.ax.set_xlabel('time [s]')
server.ax.set_ylabel('adress id')
plt.subplots_adjust( bottom=0.3)
plt.show(block=False)

server.drawing = plt.plot()

# Launch server. It will keep running unti Ctrl-C.
print "Plot Server is listening ..."
server.serve_forever()
