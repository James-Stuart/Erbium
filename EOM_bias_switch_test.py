# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 09:35:43 2018
Testing the recovery time when switching the JDSU EOM bias voltages. 
@author: James
"""

import Holeburn_james_wf as h
from HP8560E_Spectrum_Analyser import *
import pulse_blaster as pb

s = 1
ms = 1e-3
us = 1e-6
ns = 1e-9

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()



def EOM_test():
    
    h.run_offset(SpecAn)
    filepath = h.create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0)
    pb.Sequence([(['ch1'],4*s)] + [(['ch2','ch4','ch5'], 100*ms)],loop=False)
    x,y,filepath = record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = 0)