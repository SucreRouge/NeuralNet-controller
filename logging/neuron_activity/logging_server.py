import socket, SocketServer
import argparse, logging
import pickle,datetime
import pandas as pd
import numpy as np
from collections import defaultdict

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

    def process_row(self, data, hdf5_key, cache, max_cache_size):
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
             
        for key, item in data.iteritems():
            cache[key].append(item)

    def store_and_clear(self, data, hdf5_key):
        """
        Convert the cached data dict to a DataFrame and append that to HDF5.
        """
        df = pd.DataFrame(data)
        self.server.hdf_store.append(hdf5_key, df)
        data.clear()

    def handle(self):
    
        data = self.read_pickle_stream()   
        print data
        logging.debug('reading packet: %s',data)

        self.process_row(data, hdf5_key = "address", cache = self.server.cache, max_cache_size = self.server.max_cache_size)


# get the current timestamp and turn it into a string with second precision
# now = pd.Timestamp(np.datetime64(datetime.datetime.now())).strftime("%Y-%m-%d_%H:%M:%S")
now = "now"

# setup parser for command line arguments
parser = argparse.ArgumentParser(description='Real-time h5 network data storage', epilog='And this is how you log your data.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-s', '--sender_ip', metavar="", help='IP address of sending machine', type=str, default = socket.gethostname() )
parser.add_argument('-p','--port', metavar="", help='port to listen to on sending machine', type=int, default = 6000)
parser.add_argument('-f', '--h5_file', metavar="", help="file name for h5 storage", type=str, default = "h5_store_" + now +".h5"   )
parser.add_argument('-c','--cache_size', metavar="", help='wait for this number of data entries to be recieved before flushing cache to h5 store', type=int, default = 10)
parser.add_argument('-l', '--log_file', metavar="", help="file name for logs", type=str, default = "h5_store_" + now +".log"   )


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

logging.info('Starting real-time network data logging ...')
logging.info('Configuring server ...')
logging.info('Listen to ip address: %s', args.sender_ip )
logging.info('Listen to port: %s', args.port )
logging.info('Server cache size: %s', args.cache_size)
logging.info('Arriving data is logged to h5 store: %s', args.h5_file)
logging.info('Log files is specified as: %s', args.log_file)

server = SocketServer.UDPServer((args.sender_ip,args.port), DataUDPHandler)
server.cache = defaultdict(list)
server.max_cache_size = args.cache_size
server.hdf_store = pd.HDFStore(args.h5_file, "w")

logging.info('Server ready.')
server.serve_forever()
