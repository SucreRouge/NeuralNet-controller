import socket
import SocketServer
import pickle
import pandas as pd
from collections import defaultdict

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

            self.server.cache = defaultdict(list)

    def update_data_cache(self, data):

        self.flush_data_cache(max_cache_size = self.server.cache_size)

        # we grab the single element in the dict lists to avoid lists of lists
        self.server.cache["time"].append(data.keys()[0])
        self.server.cache["address"].append(data.values()[0])        

    def handle(self):
    
        data = self.read_pickle_stream()   
        
        self.update_data_cache(data)
        
        print self.server.hdf_store

    def finish(self):
        pass

host = socket.gethostname()
port = 60000

# Create the server, binding it to host and port
server = SocketServer.UDPServer((host,port), DataUDPHandler)
server.cache = defaultdict(list)
server.cache_size = 1
server.hdf_store = pd.HDFStore("test.store", "w")
# Launch server. It will keep running unti Ctrl-C.
server.serve_forever()
