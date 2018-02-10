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
## import new_1550_laser as las


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
def getTrace():
    SpecAn.write('TRA?')
    time.sleep(0.3);
    binary = SpecAn.read_raw()
    spec_data_temp = np.frombuffer(binary, '>u2')
    return spec_data_temp



    
    
if __name__ == "__main__":
    pass
    #spin_pump_seq()

##     hb.run_offset(SpecAn) #Run once
##     SIH.free_run_plot_window('Y',full_span = 'Y')
    
    
    
