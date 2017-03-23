import socket
import SocketServer
import pickle
import pandas as pd
from collections import defaultdict
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator, AutoDateFormatter
import datetime

class DataUDPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def read_pickle_stream(self):

        # print 'Server: Recieving data \t...\t',
        data = pickle.loads(self.request[0])
        # print 'done.'
        # print 'Server: data =', data  

        return data

    def send_pickle_stream(self, data):

        # print "Server: Sending answer \t...\t",
        self.request[1].sendto(pickle.dumps(data), self.client_address)
        # print "done."

    def flush_data_cache(self, max_cache_size):

        # check if cache is full, if so, make pd.series and store it, then reset cache
        if len(self.server.cache["time"]) >= max_cache_size:

            s = pd.Series(dict(zip(self.server.cache["time"], self.server.cache["address"])), name='address')
            self.server.hdf_store.append(s.name,s)
            self.server.hdf_store.flush()

            self.server.cache = defaultdict(list)

    def update_data_cache(self, data):

        self.flush_data_cache(max_cache_size = self.server.cache_size)

        # we grab the single element in the dict lists to avoid lists of lists
        self.server.cache["time"].append(data.keys()[0])
        self.server.cache["address"].append(data.values()[0])        

    def update_data_tail(self, tail_elements=10):

        if self.server.hdf_store:

            timestamps = self.server.hdf_store.select_column('address','index')
            self.server.hdf_store_tail = self.server.hdf_store.select('address',where=timestamps[-tail_elements:].index)        

    def update_tail_plot(self):

        xdata = self.server.hdf_store_tail.index
        ydata = self.server.hdf_store_tail.tolist()

        #Update data (with the new _and_ the old points)
        self.server.lines.set_xdata(xdata)
        self.server.lines.set_ydata(ydata)
        #Need both of these in order to rescale
        self.server.ax.relim()
        self.server.ax.autoscale_view()
        # Set the ticks to deal with date items
        self.server.ax.xaxis.set_major_locator(AutoDateLocator())
        self.server.ax.xaxis.set_major_formatter( DateFormatter( '%H:%M:%S:%f' ) )
        #We need to draw *and* flush
        self.server.fig.canvas.draw()
        self.server.fig.canvas.flush_events()

    def handle(self):
    
        data = self.read_pickle_stream()   
        
        self.update_data_cache(data)
        self.update_data_tail(tail_elements=100)

        if self.server.hdf_store:

            self.update_tail_plot()

host = socket.gethostname()
port = 60000

# Create the server, binding it to host and port
server = SocketServer.UDPServer((host,port), DataUDPHandler)
server.cache = defaultdict(list)
server.cache_size = 1
server.hdf_store = pd.HDFStore("test.h5", "w")
server.hdf_store_tail = pd.Series()

# Prepare stuff for plotting
server.fig, server.ax = plt.subplots(1, 1)
server.lines, = server.ax.plot([],[], '+')
server.ax.set_autoscaley_on(True)

plt.xticks(rotation=45)
server.ax.set_xlabel('time')
server.ax.set_ylabel('adress id')
plt.subplots_adjust( bottom=0.3)
plt.show(block=False)

server.drawing = plt.plot()

# Launch server. It will keep running unti Ctrl-C.
print "Plot Server is listening ..."
server.serve_forever()
