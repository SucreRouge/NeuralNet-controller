import socket, SocketServer
import argparse, logging, sys
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
    def handle(self):
    
        logging.debug("Starting handler.")

        data = pickle.loads(self.request[0])  
        logging.debug('reading data as: %s',data)

        if self.server.cache.keys():
            cache_keys = self.server.cache.keys()
            first_key = cache_keys[0]
            size = len(self.server.cache[first_key])

        else:
            size = 0

        logging.debug("Cache size: %s", size)

        if size >= self.server.max_cache_size:
            logging.debug("Writing to h5 store and flushing cache.")
            df = pd.DataFrame(self.server.cache)
            self.server.hdf_store.append(self.server.hdf5_key, df)
            self.server.cache.clear()

        for key, item in data.iteritems():
            self.server.cache[key].append(item)

        logging.debug("Finishing handler.")

# get the current timestamp and turn it into a string with second precision
# now = pd.Timestamp(np.datetime64(datetime.datetime.now())).strftime("%Y-%m-%d_%H:%M:%S")
now = ""

# setup parser for command line arguments
parser = argparse.ArgumentParser(description='Real-time h5 network data storage', epilog='... now this is how you log your data.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-s', '--sender_ip', metavar="", help='IP address of sending machine', type=str, default = socket.gethostname() )
parser.add_argument('-p','--port', metavar="", help='port to listen to on sending machine', type=int, default = 60000)
parser.add_argument('-f', '--h5_file', metavar="", help="file for h5 storage opened as", type=str, default = "h5_store_" + now +".h5"   )
parser.add_argument('-k', '--h5_key', metavar="", help="h5 storage key", type=str, default = "address")
parser.add_argument('-c','--cache_size', metavar="", help='wait for this number of data entries to be recieved before flushing cache to h5 store', type=int, default = 10)
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

logging.info('Starting real-time network data logging ...')
logging.info('Configuring server ...')
logging.info('Listen to ip address: %s', args.sender_ip )
logging.info('Listen to port: %s', args.port )
logging.info('Server cache size: %s', args.cache_size)
logging.info('Arriving data is logged to h5 store: %s', args.h5_file)
logging.info('Selected h5 key: %s', args.h5_key)
logging.info('Log files is specified as: %s', args.log_file)

try:
    server = SocketServer.UDPServer((args.sender_ip,args.port), DataUDPHandler)
    server.cache = defaultdict(list)
    server.max_cache_size = args.cache_size
    server.hdf5_key = args.h5_key
    server.hdf_store = pd.HDFStore(args.h5_file, "w")

    logging.info('Server ready.')
    logging.info('Server listening ...')
   
except Exception as e:
    logging.exception('Server setup failed.')
    sys.exit(1)

try:
    server.serve_forever()

except Exception as e:
    logging.exception('Exception in server.serve_forever()')
    sys.exit(1)

