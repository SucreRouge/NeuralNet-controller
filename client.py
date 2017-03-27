import socket
import numpy as np
import pickle

from helpers import *
  

cam_data = np.zeros((8192,3), dtype=int)
# cam_data = "testsatad"

# host = '161.122.21.47'
host = 'localhost'
port = 7777
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host,port))

try:

    send_pickle_stream(cam_data, sock)
    print "Client: Waiting for answer \t...\t"
    answer = read_pickle_stream(sock)
    
finally:
    sock.close()

