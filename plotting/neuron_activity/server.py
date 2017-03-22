import socket
import SocketServer
import pickle

class DataUDPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def read_pickle_stream(self):

        print 'Server: Recieving data \t...\t',
        data = pickle.loads(self.request[0])
        print 'done.'
        print 'Server: data =', data  

        return data

    def send_pickle_stream(self, data):

        print "Server: Sending answer \t...\t",
        self.request[1].sendto(pickle.dumps(data), self.client_address)
        print "done."

    def handle(self):
    
        data = self.read_pickle_stream()
        self.send_pickle_stream(data)
   

host = socket.gethostname()
port = 60000

# Create the server, binding it to host and port
server = SocketServer.UDPServer((host,port), DataUDPHandler)

# Launch server. It will keep running unti Ctrl-C.
server.serve_forever()
