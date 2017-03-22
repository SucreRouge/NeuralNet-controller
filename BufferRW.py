import numpy as np
import sys

"""
    Information sent to FPGA is written into SIPO (Serial In Parallel Out) buffer.
    SIPO (256 bit) content is distributed as follows:
        [255:141] - NOT USED
        [140:0]   - PARAMETERS
        [33:13]   - CAM DATA
        [12:0]    - CAM/SYNAPSE ADDRESS
    Note: Overlaping bits between PARAMETERS and CAM DATA/ADDRESS are routed depending on 'write_sel' bit.

    FPGA returns PISO (Parallel In Serial Out) buffer content.
    Total 256 bits:
        [255:173] - NOT USED
        [172:32]  - PARAMETERS
        [31:11]   - CAM DATA. [31:22] - PRE, [21:12] - POST, [11] - EXC/INH
        [10:0]    - SYNAPTIC WEIGHT

"""


def Construct_PARAMETERS(params, lengths):
    """
    Constructs 256 bit binary SIPO buffer content from parameter values passed in 'params' array.
    Array 'lengths' indicates how many bits are reserved for each of the corresponding parameters in 'params' array.
    
    Note: Only 141 bit [140:0] is taken by the data. The rest are zeros.
    
    PARAMETERS:
        
        [159:152] UP    -- NOT USED NOW
        [151:141] INI_W -- NOT USED NOW
        [140:116] TAU
        [115:102] THR
        [101:88]  INH_W
        [87:74]   EXT_W
        [73:49]   TAU_PRE
        [48:24]   TAU_POST
        [23:20]   AP
        [19:16]   AD
        [15:8]    AP_MAX
        [7:0]     AD_MAX
    """
    data = np.zeros(256, dtype = bool)
    
    for i in range(len(params)): ## Here we check if parameters do not exceed their binary spaces.
        param_bin = bin(params[i])[2:]
        if len(param_bin) > lengths[i]:
             print 'ERROR: Value', params[i], 'cannot be converted into a', lengths[i], 'bit binary number. Maximum encodable number is', 2**lengths[i]-1,'.'
             sys.exit()
    print 'No errors in parameter values were found.'

    count = 0
    for i in range(len(params)):
        temp = bin(params[i])[2:]     ## Converting i-th parameter to binary
        for ii in range(len(temp)):
            data[255-count-ii] = int(temp[len(temp)-1-ii])    ## Writing parameters into the BUFFER so that LSB of AD_MAX is at BUFFER[255]
        count += lengths[i]     ## Leaving zeros if parameter takes less binary space than is provided for it
    return data


def Construct_CAM(cam_data):
    """
    Constructs 8192x21 binary CAM table to be written into FPGA.
    8192 rows correspond to 13bit address space.
    21 columns are divided in the following way (Python array indexes): [0:9] PRE_ADR, [10:19] POST_ADR, [20] INH_BIT
    
    """
    data = np.zeros((8192,21), dtype = bool)
    
    for i in range(len(data)):
        pre_adr = bin(cam_data[i,0])[2:]
        post_adr = bin(cam_data[i,1])[2:]
        for ii in range(len(pre_adr)):
            data[i,9-ii] = int(pre_adr[len(pre_adr)-1-ii])
        for ii in range(len(post_adr)):
            data[i,19-ii] = int(post_adr[len(post_adr)-1-ii])   
        data[i,20] = int(cam_data[i,2])
    return data
 
    
def Reconstruct_PARAMETERS(buf, lengths):
    """
    Reconstructs PARAMETER values from the 256 bit binary PISO array received from FPGA (via RPi). 
    Array 'lenghts' is used for splitting the buffer into separate parameter sections.
    
    Note: Parameter values occupy PISO[172:32] bits, corresponding to Python array indexes [255-172:255-32] = [83:224]
    
    """
    count = 0
    data = []
    param_buf = buf[83:224]; len_param = len(param_buf)
    for i in range(len(lengths)):
        temp = param_buf[len_param-count-lengths[i]:len_param-count]
        temp_dec = 0
        for ii in range(lengths[i]):
            temp_dec += 2**ii*temp[lengths[i]-ii-1]
        data.append(temp_dec)
        count += lengths[i]
    return data


def Reconstruct_CAM(cam_bin):
    """
    Reconstructs decimal CAM table from the binary array received from FPGA (via RPi).
    
    """
    cam_dec = np.zeros((8192,3), dtype=int)
    
    for i in range(8192):
        for ii in range(10):
            cam_dec[i,0] += 2**ii*cam_bin[i,10-ii-1]
            cam_dec[i,1] += 2**ii*cam_bin[i,20-ii-1]
        cam_dec[i,2] = cam_bin[i,20]
    return cam_dec
        
        
def Reconstruct_WEIGHTS(weights_bin):
    """
    Reconstructs decimal WEIGHT array from binary array received from FPGA (via RPi).
    Maximum size of the array is 8192 (13bit address space), however only parts of the array can be passed.
    
    """
    weights_dec = np.zeros((len(weights_bin)), dtype = int)        
        
    for i in range(len(weights_bin)):
        for ii in range(10):
            weights_dec[i] += 2**ii*weights_bin[i,10-ii-1]
    return weights_dec
        
        
        
        
#to_FPGA = Construct_paramBuf(params, lengths)
#from_FPGA = Deconstruct_params(to_FPGA, lengths)