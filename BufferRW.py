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

BUF_SIZE = 256  ## Buffer size
NADR_WIDTH = 10 ## Neuron address space
SADR_WIDTH = 13 ## Synapse (and CAM) address space

WEIGHT_SIZE = 11 ## Synaptic weight size in bits

CAM_READ = 2**SADR_WIDTH ## How many CAM rows to read?


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
    buf_data = np.zeros(BUF_SIZE, dtype = int)
    
    for i in range(len(params)): ## Here we check if parameters do not exceed their binary spaces.
        param_bin = bin(params[i])[2:]
        if len(param_bin) > lengths[i]:
             print 'ERROR: Value', params[i], 'cannot be converted into ', lengths[i], 'bit binary number. Maximum encodable number is', 2**lengths[i]-1,'.'
             sys.exit()
    print 'No errors in parameter values were found.'

    pointer = 0
    param_str = ''
    for i in range(len(params)):
        param_str += ('{0:0' + str(lengths[i]) + 'b}').format(params[i])
        pointer += lengths[i]
        
    buf_data[BUF_SIZE-sum(lengths):] = map(int, list(param_str))
    return buf_data


def Construct_CAM(cam_data):
    """
    Constructs 8192x21 binary CAM table to be written into FPGA.
    8192 rows correspond to 13bit address space.
    21 columns are divided in the following way (Python array indexes): [0:9] PRE_ADR, [10:19] POST_ADR, [20] INH_BIT
    
    """
    cam_array = np.zeros((2**SADR_WIDTH, 2*NADR_WIDTH+1), dtype = int)

    for i in range(len(cam_array)):
        pre_adr = ('{0:0' + str(NADR_WIDTH) + 'b}').format(cam_data[i,0])
        post_adr = ('{0:0' + str(NADR_WIDTH) + 'b}').format(cam_data[i,1])
        inh_bit = str(cam_data[i,2])
        cam_row = pre_adr + post_adr + inh_bit
        cam_array[i] = map(int, list(cam_row))
                
    return cam_array


def Construct_WEIGHTS(syn_data, const = True):
    """
    Constructs 8192x11 binary WEIGHT table to initiate synaptic weights.
    const = True/False indicates whether syn_data is a constant initial weight for all synapses, or array of individual values.
    
    """
    syn_array = np.zeros((2**SADR_WIDTH, 11), dtype = int)
    
    if const == True:
        if syn_data >= 2**11:
            print 'ERROR: Value', syn_data, 'cannot be converted into 11 bit binary number. Maximum encodable number is', 2**11-1,'.'
            sys.exit()
    
    for i in range(len(syn_array)):
        if const == True:
            weight = '{0:011b}'.format(syn_data)
        else:
            if syn_data[i] >= 2**11:
                print 'ERROR: Value', syn_data[i], 'cannot be converted into 11 bit binary number. Maximum encodable number is', 2**11-1,'.'
                sys.exit()
            weight = '{0:011b}'.format(syn_data[i])
        syn_array[i] = map(int, list(weight))
    
    return syn_array

    
def Reconstruct_PARAMETERS(param_bin, lengths):
    """
    Reconstructs PARAMETER values from trimmed 256 bit binary PISO array received from FPGA (via RPi). 
    Array 'lenghts' is used for splitting the buffer into separate parameter sections.
    
    Note: Parameter values occupy PISO[172:32] bits, corresponding to Python array indexes [255-172:255-32] = [83:224]
    
    IMPORTANT: This function expects ONLY the PARAMETER part of the PISO !
    
    """
    if len(param_bin) != sum(lengths):
        print 'ERROR: Length of the passed binary array (', len(param_bin), ') does not match the sum of expected parameter lengths (', sum(lengths), ').'
        sys.exit()
    
    pointer = 0
    param_dec = []
#    param_bin = buf[83:224]; ## WEIGHT - 11bits, CAM_DATA - 21bit ---> 224 = 256-11-21; 83 = 256-11-21-141.
    for i in range(len(lengths)):
        temp_bin = ''.join(str(int(k)) for k in param_bin[pointer:pointer + lengths[i]])
        temp_dec = int(temp_bin, 2)
        
        param_dec.append(temp_dec)
        pointer += lengths[i]
    return param_dec


def Reconstruct_CAM(cam_bin):
    """
    Reconstructs decimal CAM table from the binary array received from FPGA (via RPi).
    
    """
    cam_dec = np.zeros((2**SADR_WIDTH,3), dtype = int)
    
    for i in range(CAM_READ):
        pre_adr = ''.join(str(int(k)) for k in cam_bin[i, 0:NADR_WIDTH])
        post_adr = ''.join(str(int(k)) for k in cam_bin[i, NADR_WIDTH:2*NADR_WIDTH])
        
        cam_dec[i,0] = int(pre_adr, 2)
        cam_dec[i,1] = int(post_adr, 2)
        cam_dec[i,2] = int(cam_bin[i, 2*NADR_WIDTH])
    return cam_dec
        
        
def Reconstruct_WEIGHTS(weights_bin):
    """
    Reconstructs decimal WEIGHT array from binary array received from FPGA (via RPi).
    Maximum size of the array is 8192 (13bit address space), however only parts of the array can be passed.
    
    """
    weights_dec = np.zeros((len(weights_bin)), dtype = int)        
        
    for i in range(len(weights_bin)):
        weight_str = ''.join(str(int(k)) for k in weights_bin[i])
        weights_dec[i] = int(weight_str, 2)
    return weights_dec
        








