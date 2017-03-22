import socket
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
    # closing socket for sending, i.e. prepare for recieving an answer
    sock.shutdown(socket.SHUT_WR)
    print "done."