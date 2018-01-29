# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 11:44:30 2018
This code is set up for the AFC experiment and utilises code from Milos and myself,
such as holeburn_james_wf and the Hp spectrum analyzer/ pulse blaster codes
@author: James
"""
from HP8560E_Spectrum_Analyser import *
import HP_Spectrum_Analyser as HP
import os
import time
import pylab
from time import sleep
from datetime import datetime
import datetime
import binascii
import numpy as np
import matplotlib.pyplot as plt
import pulse_blaster as pb
import spectrum_image_HP8560E as SIH
import Stanford_FG as stan
import windfreakV2 as wf
import Holeburn_james_wf3 as hb


Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

hour = 3600
min = 60
s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()





def multi_record(SpecAn,d_time,n):
    '''Takes 'n' scans on the HP Spectrum Analyzer at ~d_time intervals.
       This is an augmented version of record_trace from holeburn_james.'''
    #Run the following first to set up the text file.
    #hb.create_file(SpecAn, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = '')

    SpecAn.write('SP?')
    span = float(SpecAn.read())  
    SpecAn.write('CF?')
    center = float(SpecAn.read())   
     
    file = open(filepath,'a')
    x = np.linspace(center - span/2, center + span/2, 601)
    spec_data_db = np.zeros((601,n)
    
    for i in range(n):
        SpecAn.write('TS')
        #Waits for Spectrum Analyser to finish Data sweep
        SpecAn.wait_for_srq(timeout = 30000)

      
        #Gets the trace from the SpecAn
        SpecAn.write('TRA?')
        binary = SpecAn.read_raw()
        spec_data_temp = np.frombuffer(binary, '>u2') # Data format is big-endian unsigned integers
        
        
        spec_data_db(:,i) = SIH.convert2db(SpecAn,spec_data_temp)
        
        if compensated == 'Y':
            spec_data_db(:,i) = compensate(spec_data_temp, span)
        
        SpecAn.write("CLEAR; RQS 4")
        pb.Sequence([(['ch2','ch5'],d_time)],[(['ch2','ch5','ch4'],1*ms)],loop=False)
    
    #Conjoins both x and spec_data_temp vectors and saves them to file     
    data = np.vstack([x, spec_data_db]).T
    np.savetxt(file, data, fmt='%.10e')
     
             
    file.close()
    pylab.ion()
 
    if sweep_again == 'Y':
        HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
        
    return x, spec_data_db, filepath     