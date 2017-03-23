import socket, datetime
import numpy as np
import pandas as pd
import pickle
from random import randint

def read_pickle_stream(sock):

    print 'Client: Recieving data \t...\t',
    data_string = sock.recv(4096)
    data = pickle.loads(data_string)
    print 'done.'
    print 'Client: data =', data  

    return data

def send_pickle_stream(data, sock, target):

    data_string = pickle.dumps(data)
    print "Client: Sending data \t...\t",
    sock.sendto(data_string, target)
    print "done."

host = socket.gethostname()
port = 60000
dimension = 4*4 - 1

# Create a socket (SOCK_DGRAM means a UPD socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
   
    for i in range(5):
		
   		address = randint(0,dimension)
   		time_stamp = pd.Timestamp(np.datetime64(datetime.datetime.now()))

   		data = { "time": time_stamp, "address": address }

		send_pickle_stream(data, sock, target= (host,port))
		# answer = read_pickle_stream(sock)
		
finally:
    sock.close()

