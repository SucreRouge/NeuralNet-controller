import socket
import numpy as np
import pickle

from BufferRW import *
from helpers import *


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


cam_silly = np.zeros((8192,3), dtype=int)
inh_bit = 0
for i in range(1023):
    cam_silly[i,0] = i
    cam_silly[i,1] = i+1
    cam_silly[i,2] = inh_bit
    if inh_bit == 1:
        inh_bit = 0
    else: inh_bit = 1


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
command = {'rc':0, 'wc':1, 'rp':2, 'wp':3, 'rw':4, 'ww':5}

host = '161.122.21.47'
port = 7777
#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.connect((host,port))

param_data = Construct_PARAMETERS(params, lengths)
cam_data = Construct_CAM(cam_silly)
syn_data = Construct_WEIGHTS(1000, const=True)


while True:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    x = raw_input('Input command to execute: ')
    
    if x == 'rc':
        sock.connect((host,port))
        send_pickle_stream([command['rc']], sock)
        answer = read_pickle_stream(sock)
        cam = Reconstruct_CAM(answer)
        sock.close()
    
    elif x == 'wc':
        sock.connect((host,port))
        send_pickle_stream([command['wc'], cam_data], sock)
        print 'Done sending CAM data.'
        sock.close()
        
    elif x == 'rp':
        sock.connect((host,port))
        send_pickle_stream([command['rp']], sock)
        answer = read_pickle_stream(sock)
        print Reconstruct_PARAMETERS(answer[BUF_SIZE-sum(lengths):], lengths)
        sock.close()
    
    elif x == 'wp':
        sock.connect((host,port))
        send_pickle_stream([command['wp'], param_data], sock)
        answer = read_pickle_stream(sock)
        print 'Written parameters:', Reconstruct_PARAMETERS(answer[BUF_SIZE-sum(lengths):], lengths)
        sock.close()
        
    elif x == 'rw':
        sock.connect((host,port))
        send_pickle_stream([command['rw']], sock)
        answer = read_pickle_stream(sock)
        weights = Reconstruct_WEIGHTS(answer)
        sock.close()
        
    elif x == 'ww':
        sock.connect((host,port))
        send_pickle_stream([command['ww'], syn_data], sock)
        print 'Done sending weights.'
        sock.close()
        
    elif x == 'quit':
        break
        
    else:
        print 'Unknwon command. Available commands: rc, wc, rp, wp, rw, ww.'


