import socket
import numpy as np
import pickle
<<<<<<< Updated upstream
import BufferRW as bf
=======
from BufferRW import *
from helpers import *
>>>>>>> Stashed changes

CLK = int(100e6) ## CLOCK speed in FPGA

TAU = int(20e-3*CLK*np.log(2))         ## (0 - 16,777,215) 25bits
THR = 8000                             ## (0 - 16,383) 14bits
INH_W = 200                            ## (0 - 16,383) 14bits
EXT_W = 8000                           ## (0 - 16,383) 14bits                   
TAU_PRE = int(20e-3*CLK*np.log(2))     ## (0 - 16,777,215) 25bits
TAU_POST = int(80e-3*CLK*np.log(2))    ## (0 - 16,777,215) 25bits
AP = 6                                 ## (0 - 15) 4bits
AD = 3                                 ## (0 - 15) 4bits
AP_MAX = 60                            ## (0 - 255) 8bits
AD_MAX = 30                            ## (0 - 15) 8bits

params = [TAU, THR, INH_W, EXT_W, TAU_PRE, TAU_POST, AP, AD, AP_MAX, AD_MAX]
lengths = [25, 14, 14, 14, 25, 25, 4, 4, 8, 8]

cam_data = np.zeros((8192,3), dtype=int)
inh_bit = 0
for i in range(1023):
    cam_data[i,0] = i
    cam_data[i,1] = i+1
    cam_data[i,2] = inh_bit
    if inh_bit == 1:
        inh_bit = 0
    else: inh_bit = 1
    
test = Construct_CAM(cam_data)
test_dec = Reconstruct_CAM(test)

"""
    This program passes and receives binarry arrays to and from RPi.
    Arrays possible for passing: PARAMETERS, CAM DATA ARRAY.
    Arrays possible for receiving: PARAMETERS, CAM DATA ARRAY, SYNAPTIC WEIGHTS.
    
    First digit in the passed data corresponds the following commands, defined in the dictionary 'command':
        0 - 'rc' - read CAM
        1 - 'wc' - write CAM (CAM DATA is sent after these two symbols)
        2 - 'rp' - read PARAMETERS
        3 - 'wp' - write PARAMETERS (PARAMETERS are sent after these two symbols)
        4 - 'rw' - read SYNAPTIC WEIGHTS
"""
command = {'rc':0, 'wc':1, 'rp':2, 'wp':3, 'rw':4, 'connection':5}

host = '161.122.21.47'
port = 7777
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host,port))

try:

    paramBuf = Construct_PARAMETERS(params, lengths)
    send_pickle_stream([command['rc'], test], sock)

    answer = read_pickle_stream(sock)
#    print Reconstruct_PARAMETERS(answer[BUF_SIZE-sum(lengths):], lengths)
finally:
    sock.close()

