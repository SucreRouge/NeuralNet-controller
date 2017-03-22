import socket
import numpy as np
import pickle

def read_pickle_stream(socket):

    print 'Client: Recieving data \t...\t',

    serialized_data = ''
    while True:
        chunk = socket.recv(1024)
        if not chunk:
            break
        serialized_data += chunk

    data = pickle.loads(serialized_data)
    print 'done.'
    print 'Client: data =', data  

    return data

def send_pickle_stream(data, socket):

    data_string = pickle.dumps(data)
    print "Client: Sending data \t...\t",
    sock.sendall(data_string)
    # closing socket for sending, i.e. prepare for recieving answer
    sock.shutdown(socket.SHUT_WR)
    print "done."
   

cam_data = np.zeros((8192,3), dtype=int)
# cam_data = "testsatad"

# host = '161.122.21.47'
host = 'localhost'
port = 7777
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host,port))

try:

    send_pickle_stream(cam_data, socket)
    print "Client: Waiting for answer \t...\t"
    answer = read_pickle_stream(sock)
    
finally:
    sock.close()

