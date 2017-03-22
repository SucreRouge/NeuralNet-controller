import pyqtgraph as pg
#from pyqtgraph.Qt import QtCore, QtGui

from socket import *
import struct
import numpy as np

"""
    This script reads jAER events through UDP, downscales the image (from 130x130 to lower)
    and sends the postprocessed events to Raspberry Pi through TCP stream.
    
    DVS128 packet format (16 bits per event):
        [15]   External event
        [14:8] Y address
        [7:1]  X address
        [0]    Polarity
        
"""

""" Local connection to DVS128 """
host='127.0.0.1'; port=7777; buf_size=63000; num_read=1
DVS_socket = socket(AF_INET, SOCK_DGRAM)
DVS_socket.bind((host, port))

""" Remote connection to Raspberry Pi """
server='161.122.21.47'; s_port=6666
Pi_socket = socket(AF_INET, SOCK_DGRAM)
#Pi_socket.connect((server, s_port))

print 'Connected to the server on ', server

new_size = 10 # compressing 130x130 into new_size x new_size
matrix = np.zeros((new_size,new_size))

xmask = 0x00FE ## 0111_1111_0000_0000
xshift = 1
ymask = 0x7F00 ## 0000_0000_1111_1110
yshift = 8
pmask = 0x1 ## 0000_0000_0000_0001
pshift = 0

inc_str = 0; inc_int=0; count_inc=0; count_out=0;
def UDP_jAER():
    global inc_str, inc_int, count_inc, count_out
    #matrix = np.zeros((new_size,new_size))
    spike_matrix = np.zeros((new_size,new_size))
    
    for this_read in range(num_read):
        data = DVS_socket.recv(buf_size)
        
        counter = 4
        while(counter < len(data)):
            addr = struct.unpack('>I', data[counter:counter + 4])[0]
            counter = counter + 8

            x_addr = (addr & xmask) >> xshift
            y_addr = (addr & ymask) >> yshift
            #a_pol = (addr & pmask) >> pshift
            
            neur_x = int(x_addr*new_size/130)
            neur_y = int(y_addr*new_size/130)

            matrix[neur_y,neur_x] += 1
            if matrix[neur_y,neur_x] == 70: ## THRESHOLD value. Change to change firing rate
                matrix[neur_y,neur_x] = 0
                spike_matrix[neur_y,neur_x] = 1
#                Pi_socket.sendto(str(neur_x)+' '+str(neur_y)+' ', (server, s_port)) #With each spike Pi receives something like '10 12 '
#                Pi_socket.send(str(neur_x)+' '+str(neur_y)+' \n') #With each spike Pi receives something like '10 12 '
                count_out += 1
#                inc_str = Pi_socket.recv(1024)
#                inc_int = map(int, inc_str[0:len(inc_str)-1].split(' '))
#                count_inc += len(inc_int)
    win.setImage(spike_matrix, autoRange=True)
    pg.QtGui.QApplication.processEvents()


""" Here we initialize the plot window and plotting colors. """
pos = np.array([0.0, 1.0])
color = np.array([[0,0,255,255], [255,0,0,255]])#, dtype=np.ubyte)
color_map = pg.ColorMap(pos, color, mode=None)

win = pg.image(matrix)
win.view.setAspectLocked(False)
win.setColorMap(color_map)
win.resize(700,500)

while True:
    UDP_jAER()
#finally:
#    DVS_socket.close()
#    Pi_socket.close()
    
    
    
    
    
    
    
    
    
    
    
    
    