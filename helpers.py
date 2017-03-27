import socket
import pickle

def read_pickle_stream(sock):

#    print 'Client: Recieving data \t...\t',

    serialized_data = ''
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        serialized_data += chunk

    data = pickle.loads(serialized_data)
    print 'Status: Received data =', data  

    return data

def send_pickle_stream(data, sock):

    data_string = pickle.dumps(data)
    print "Status: Sending instruction",data[0],"and data \t...\t",
    sock.sendall(data_string)
    # closing socket for sending, i.e. prepare for recieving an answer
    sock.shutdown(socket.SHUT_WR)
    print "Done."