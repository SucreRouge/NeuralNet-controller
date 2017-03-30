import socket, datetime
import numpy as np
import pandas as pd
import pickle
from random import randint
from time import sleep
from collections import OrderedDict

def send_pickle_stream(data, sock, target):

    data_string = pickle.dumps(data)
    sock.sendto(data_string, target)
  
def prepare_packet_data(address, event_id, initial_time_stamp):

	now_time_stamp = pd.Timestamp(np.datetime64(datetime.datetime.now()))
	elapsed_time = now_time_stamp - initial_time_stamp
	
	data = OrderedDict()
	data["event_id"] = event_id
	data["timestamp"] = now_time_stamp
	data["timedelta"] = elapsed_time
	data["address"] = address

	

	return data

host = socket.gethostname()
port = 60000
dimension = 30*30 - 1

# Create a socket (SOCK_DGRAM means a UPD socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

initial_time_stamp = pd.Timestamp(np.datetime64(datetime.datetime.now()))
event_id = long(0)

try:
  
	for wait in np.random.gamma(10, 10, 10):

		sleep(wait*0.001)
		address = randint(0,dimension)
		data = prepare_packet_data(address,event_id,initial_time_stamp)	
		event_id += 1   
		print "Client: Sending:", event_id
		send_pickle_stream(data, sock, target= (host,port))
		
		# send signal that nothing is firing
		sleep(wait*0.001)
		address = -1
		data = prepare_packet_data(address,event_id,initial_time_stamp)
		event_id += 1   
		# print "Client: Sending:", data
		send_pickle_stream(data, sock, target= (host,port))

finally:
    sock.close()
