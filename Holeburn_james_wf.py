################################################################################
###									     ###
###		JAMES HOLE BURNING TESTING STUFF V1.0                        ###
###									     ###
################################################################################

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

import James_spin_polarize as spin


#CH1 = Windfreak
#CH2 = SpecAn HP8560E
#CH3 = VCO
#CH5 LOW = burn (Laser power should be minimum)
#CH5 HIGH = scan(Laser power with no RF should be 2/3 max power)

#CH5 is used to switch between DC voltages to EOM, this is used to change the power
#of the carrier vs the sidebands. For scanning we want weak signal, so strong carrier with weak sidebands
#However we also require that the ratio between 1st and 2nd harmonics is as small as possible to limit
#noise due to Carrier - 2nd harmonic... ect
#The other setting allows for much higher power in the sidebands to give strong hole burning. 


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


def full_sweep(SpecAn):
    ''' Sets power to minimum and span to full spectrum '''
    SpecAn.write('CF' + str(1.45*GHz))
    SpecAn.write('SP' + str(2.9*GHz))



def create_file(SpecAn, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = ''):
    ''' Creates a file based on "datestring + filename.txt"
        
        Compensated and Sweep again appear in the file header
     '''
##     
    #Date/Time information
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    usec = datetime.datetime.now().strftime("%S.%f")
    
    date_string = year + '-' + month + '-' + day
    time_string = hour + ":" + minute + "." + second
    
    #Set up filename, either simple or records time created aswell as date
##     filepath = "C:\Users\Milos\Desktop\James\\" + date_string + filename + ' ' + str(minute)+';'+str(usec) +'.txt'
    filepath = "C:\Users\Milos\Desktop\James\\" + date_string + filename +'.txt'
    try:
        os.remove(filename)
    except OSError:
        pass
    file = open(filepath,'w')
    
    #Write header
    file.write('Date: ' + date_string + '\n')
    file.write('Time: ' + time_string + '\n')
    SpecAn.write('CF?')
    center = float(SpecAn.read())
    print 'Center: ' + str(center)
    SpecAn.write('SP?')
    span = float(SpecAn.read())
    print 'Span: ' + str(span)
    file.write('Center freq: ' + str(center) + ' Span: ' + str(span) + '\n')
    SpecAn.write('RL?')
    ref_level = SpecAn.read()
    file.write('Reference Level: ' + ref_level + '\n')
    file.write('Data is offset subtracted: ' + compensated + '\n' + '\n')
    
    
    #Optional/ extra header information
    optional_header = ''
    file.write(optional_header + '\n')
    file.write('Burn time: ' + str(burn_time) + '\n')


    
    
    #From Milos's code HP8560E_Spectrum_Analyser, sets up SpecAn for a single sweep trace
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    #sets up registers to return interupt when sweep is complete
    SpecAn.write("CLEAR; RQS 4")    
    file.close()
    
    return filepath    
    



 def record_trace(SpecAn, filepath, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = ''):
     ''' Records a single trace from SpecAn '''
     SpecAn.write('SP?')
     span = float(SpecAn.read())  
     SpecAn.write('CF?')
     center = float(SpecAn.read())    
 
     SpecAn.write('TS')
     #Waits for Spectrum Analyser to finish Data sweep
     SpecAn.wait_for_srq(timeout = 30000)
 ##     import time
 ##     #time.sleep(10)
     
 
     file = open(filepath,'a')
     x = np.linspace(center - span/2, center + span/2, 601)
     spec_data_temp = np.zeros(601)
   
     #Gets the trace from the SpecAn
     SpecAn.write('TRA?')
     binary = SpecAn.read_raw()
     spec_data_temp = np.frombuffer(binary, '>u2') # Data format is big-endian unsigned integers
     
     
     spec_data_db = SIH.convert2db(SpecAn,spec_data_temp)
     
     if compensated == 'Y':
         spec_data_db = compensate(spec_data_temp, span)

     #Conjoins both x and spec_data_temp vectors and saves them to file     
     data = np.vstack([x, spec_data_db]).T
     np.savetxt(file, data, fmt='%.10e')
 
         
     file.close()
     pylab.ion()
 
     if sweep_again == 'Y':
         HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
         
     return x, spec_data_db, filepath     
     
     
def compensate(data, span):
    ''' Takes data from SpecAn trace and subtracts background from "run_offset" '''
     if span == 2900000000.0:
         save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"
     else:
         save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"   
     amplitude_offset = np.loadtxt(save_file,delimiter=",")
     compensated_data = np.subtract(data,amplitude_offset)
     
     return compensated_data
    
        
    
    
    
    
    
def background(SpecAn, freq, span, res = 10*kHz, sweep = 1*s):
    ''' Semi automates the background measurements on the HP8560E '''
    
    #First step laser off the absorption
    #Set SpecAn to be a desired freq, span...
    SpecAn.write('CF ' + freq)
    SpecAn.write('SP ' + span)
    SpecAn.write('RB ' + res)
    SpecAn.write('ST ' + sweep)
    
    #Run background measurement.
    SIH.save_offset(3)
    
    #Set span back to full so laser can be stepped back to absorption
    full_sweep(SpecAn)
    
    #Now Step laser back to absorption and Lock laser to right place
    
    
    
    
def run_offset(SpecAn, freq = 1.45*GHz, span = 2.9*GHz, res = 30*kHz, sweep = 50*ms, full_span = 'Y', show_window = 'N'):
    ''' Sets desired SpecAn settings and runs Milos's background and free run
        programs.'''
    SpecAn.write("CF " + str(freq))
    SpecAn.write("SP " + str(span))
    SpecAn.write("RB " + str(res))
    SpecAn.write("ST " + str(sweep))
    SpecAn.write('VB ' + str(1000))
    
    sleep(0.5)
    SIH.save_offset(20, full_span)
        
    if show_window == 'Y':
        SIH.free_run_plot_window('Y', freq, span, full_span)
        
        
    

def holeburn(offset = 'N', args = [1.45*GHz, 2.9*GHz, 30*kHz, 1*s]):
    ''' No longer use this '''
    if offset != ('Y' or 'N'):
        raise error('argument must be "Y" or "N"')
        
    elif offset == 'Y':
        #Set SpecAn stuff
        SpecAn.write("CF " + str(args[0]))
        SpecAn.write("SP " + str(args[1]))
        SpecAn.write("RB " + str(args[2]))
        SpecAn.write("ST " + str(args[3]))
        sleep(0.5)
        SIH.save_offset(20)
        
    pb.hole_burn(3*s)
    SIH.free_run_plot_window('Y')
#    


 

def repump_sequence(SpecAn, SpecAn_Bool, start_freq, stop_freq, sweep_time = 200*ms):
    ''' After hole burning this will hopefully return atoms to 'normal' state. '''

    sweep_array = np.array([[start_freq, stop_freq, sweep_time]])
    [Stanford_FG, Stanford_Bool] = stan.Initialise_Stanford_FG()    
    
    #Tell me the Stanfords settings
    Stanford_FG.write('AMPL?')
    print 'Amplitude set to ' + Stanford_FG.read()    
    Stanford_FG.write('OFFS?')
    print 'Offset set to ' + Stanford_FG.read()    
    
    #set up and upload sweep array to stanford
    [num_array, waveform_length] = stan.VCO_Sweep(sweep_array, Stanford_FG, Stanford_Bool, 'op amp', SpecAn, SpecAn_Bool)
    stan.Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
    #Set pulseblaster to run VCO via ch3
    pb.repump()




def spin_polarise(SpecAn, SpecAn_Bool, start_freq, pumps = 10, direction = 'backwards'):
    ''' Controls stanford plugged into VCO to spin pump ensomble by scanning over
    delta m = +/-1. 
    MIN FREQ: 1900MHz'''
    sweep_time = 50*ms
    sweep_array = np.array([[start_freq, start_freq + 800*MHz, sweep_time]]) 
    #Best time scale is 100ms sweep time - Milos
    print 'Sweep range: ' + str(np.min(sweep_array)) +', '+ str(np.max(sweep_array)/1e6)
    [Stanford_FG, Stanford_Bool] = stan.Initialise_Stanford_FG()
    
    #Tell me the Stanfords settings
    Stanford_FG.write('AMPL?')
    print 'Amplitude set to ' + Stanford_FG.read()    
    Stanford_FG.write('OFFS?')
    print 'Offset set to ' + Stanford_FG.read() 
    
    if direction == 'backwards':
        [num_array, waveform_length] = stan.VCO_Sweep_backwards(sweep_array, Stanford_FG, Stanford_Bool, 'op amp 3.7', SpecAn, SpecAn_Bool)
    elif direction == 'forwards':
        [num_array, waveform_length] = stan.VCO_Sweep(sweep_array, Stanford_FG, Stanford_Bool, 'op amp 3.7', SpecAn, SpecAn_Bool)
    else:
        raise error('direction must be either backwards or forwards')
        
    stan.Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
    #Sets pulseblaster to run VCO via ch3
    time = pumps*sweep_time
    print 'Spin polarizing for: ' + str(time) + ' seconds'
    
    array = create_sequence(time)
    pb.Sequence(array,loop=False) 
    
    
    
def create_sequence(time):
    ''' Takes in the 'time' for the spin polarizing and creates an appropriate 
    pulse blaster array'''
    if time > 10: #Pulseblaster does not like values above 10s
        no_of_loops = int(time)/10
        remainder = round(time%10,3)
        array = []
        
        for i in range(no_of_loops):
            array = [(['ch3'], 10*s)] + array
        if remainder > 0:
            array = array + [(['ch3'],remainder)] + [(['ch2','ch5'], 1*ms)]
        else:
            array = array + [(['ch2','ch5'], 1*ms)]

    else:
        array = [(['ch3'],time)] + [(['ch2','ch5'], 1*ms)]
        
    return array
    



def windfreak(freq, dB, power_state, filepath, talk = 'YES', write = 0):
    ''' Basic Windfreak V2 control, sets frequency, and power (controling whether
        it's in high or low power mode too). And writes WF power settings into file.
        freq: 0 - 4.4GHz in Hz
        dB: -31 - 0
        power_state: 'high','low'
    '''
    if freq <= 4.4e9 and 0 <= freq:
        pass
    else:
        raise('error: freq must be within 0 - 4.4GHz')
    if dB <= 0 and -31.5 <= freq:
        pass
    else:
        raise('error: dB must be within 0 - -31.5')
    if power_state in ['high','low']:
        power_state_binary = 1 if power_state == 'high' else 0
    else:
        raise('error: power state must be "high" or "low"')            
    
    instr,bSuccess = wf.Initialise_Windfreak()
    wf_freq = wf.Windfreak_freq(freq, talk, instr) #Sets WF freq and records the set freq  
    
    dB_63 = 2*dB + 63 
    wf_power_63 = wf.Windfreak_power_level(dB_63, talk, instr)
    wf_power = (wf_power_63 - 63)/2
    
    wf_power_state_binary = wf.Windfreak_HILO(power_state_binary, talk, instr)
    wf_power_state = ' high' if wf_power_state_binary == 1 else ' low' 
    
    if write == 1:
        #open hole burning data file and replace line 7 with WF settings
        file = open(filepath,'r+')
        data = file.readlines()
        file.seek(0)
        data[6] = 'WF power: ' + str(wf_power)  + str(wf_power_state) 
        file.writelines(data)
        file.close()
    

def full_offset(SpecAn, freq = 1*GHz):
    ''' Runs offsets for two frequency ranges, full span 0 - 2.9 GHz and a smaller
    offset 0 - freq.'''
    full_sweep(SpecAn)
    run_offset(SpecAn, full_span = 'Y')
    sleep(0.1)
    
    s = freq
    f = freq/2
    run_offset(SpecAn, freq = f, span = s, full_span = 'N')
    sleep(0.1)
    
    full_sweep(SpecAn)
##     SIH.free_run_plot_window('Y',full_span = 'Y')
##     run_offset(SpecAn, freq = 1.8*GHz, span = 100*MHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N')
##     SIH.free_run_plot_window('Y', full_span = 'N')


def burn_sequence(burn, burn_freq, power, hl = 'low', record = 'True'):
    ''' Sets the Windfreak to a speficied frequency and power to burn for an alloted time.
        If record is true, then the spectrum analyser will record the resulting hole '''
    filepath = ''
    if record == 'True':
        run_offset(SpecAn, freq = burn_freq, span = 1*MHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N')
        filepath = create_file(SpecAn, compensated = 'Y', n=1, burn_time = burn)
        windfreak(burn_freq, power, hl, filepath, write = 1)
    else:
        windfreak(burn_freq, power, hl, filepath, write = 0)
    pb.hole_burn(burn)
    
    if record == 'True':
        x,y,filepath=record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = burn)
    sleep(0.5*s)


    full_sweep(SpecAn)
##     SIH.free_run_plot_window('Y',full_span = 'Y')
    if record == 'True'
        return x,y

def burn_n_sit(burn, freq1,power,hl):
    ''' Burns a hole and then increases the span to watch the hole and carrier hole move. '''
##         burn = 0.02*s
##         freq1 = 2.560*GHz
    #Hole burning sequence
    run_offset(SpecAn, freq = freq1, span = 1*MHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N')
    filepath = create_file(SpecAn, compensated = 'Y', n=1, burn_time = burn)
    windfreak(freq1, power, hl, filepath, write = 1)
    pb.hole_burn(burn)
    x,y,filepath=record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = burn)
    sleep(0.1*s)

    SpecAn.write('CF ' + str(freq1))
    SpecAn.write('SP 5000000')
    SIH.free_run_plot_window('N',full_span = 'N')    



def spin_pump_seq(freq,pumps,record = "False"):
    ''' Runs spin polarize sequence and allows for the ability to record the spectrum
        just after spin pumping.
    '''
    time = spin_polarise(SpecAn, SpecAn_Bool, freq, pumps, direction = 'forwards')
    sleep(time) #Wait for spin polarize to take place.
    
    SpecAn.write('FA ' + str(0*MHz))  #Start freq
    SpecAn.write('FB ' + str(2900*MHz))#Stop freq
    save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"
    amplitude_offset = np.loadtxt(save_file,delimiter=",")
    
    #This if statement is a rewritten version of record_trace
    if record == 'True':
        filepath = create_file(SpecAn, compensated = 'N', n=1, burn_time = 0)
        
        array = [([], 0.5*s)] + [(['ch5'], 500*ms), (['ch2','ch4','ch5'], 100*ms)] + [(['ch2','ch5'], 100*ms)]
        pb.Sequence(array,loop=False)
        
        [x,y,f] = record_trace(SpecAn, filepath, filename = '', compensated = 'Y', sweep_again = 'Y', n = 1, burn_time = 0)
        
        
def spin_jump_seq(freq = 2.4*GHz, reps = 1, record_jump = 'N'):
    ''' Spin polarize crystal into |7/2>. 
    
    Burn on the m = -1 to make a |5/2> anti hole. Burn on that hole to shift to |3/2>. 
    Repeat this to ensure max population has been shifted down to lower state. 
    '''
    freq_b = freq - 1.3*GHz #This should be the freq of the peak of the delta m = -1 |7/2>
    array = [107.9, 217]*MHz
    spin_pump_seq(freq,800,record = "False") #Spin polarize the delta m = 1 feature    
    
    if record == 'N'
        for i in range(reps): #"Spin jump" multiple times to ensure max population moved
            #Check span setting in burn_sequence (set to ~ 1MHz)
            
            if i == reps-1:
                burn_sequence(0.05,freq_b,-15,hl = 'high',record = 'False') #This should burn in the peak of the delta m = -1 |7/2>
                burn_sequence(0.05,freq_b - array[0],-15,hl = 'high',record = 'False') #Should burn on the delta m = -1 |+5/2> anti hole
                burn_sequence(0.05,freq_b - array[1],-15,hl = 'high',record = 'True') #Should burn on the delta m = -1 |+3/2> anti hole
            else:
                burn_sequence(0.05,freq_b,-15,hl = 'high',record = 'False') #This should burn in the peak of the delta m = -1 |7/2>
                burn_sequence(0.05,freq_b - array[0],-15,hl = 'high',record = 'False') #Should burn on the delta m = -1 |+5/2> anti hole
                burn_sequence(0.05,freq_b - array[1],-15,hl = 'high',record = 'False') #Should burn on the delta m = -1 |+3/2> anti hole
    else:
        for i in range(reps): #"Spin jump" multiple times to ensure max population moved
            #Check span setting in burn_sequence (set to ~ 1MHz)
            
            if i == reps-1:
                burn_sequence(0.05,freq_b,-15,hl = 'high',record = 'True', filename = '1') #This should burn in the peak of the delta m = -1 |7/2>
                burn_sequence(0.05,freq_b - array[0],-15,hl = 'high',record = 'True', filename = '2') #Should burn on the delta m = -1 |+5/2> anti hole
                burn_sequence(0.05,freq_b - array[1],-15,hl = 'high',record = 'True', filename = '3') #Should burn on the delta m = -1 |+3/2> anti hole
            else:
                burn_sequence(0.05,freq_b,-15,hl = 'high',record = 'False') #This should burn in the peak of the delta m = -1 |7/2>
                burn_sequence(0.05,freq_b - array[0],-15,hl = 'high',record = 'False') #Should burn on the delta m = -1 |+5/2> anti hole
                burn_sequence(0.05,freq_b - array[1],-15,hl = 'high',record = 'False') #Should burn on the delta m = -1 |+3/2> anti hole
                
        
    sleep(1)
    SIH.free_run_plot_window('N',full_span = 'N')

 

    
if __name__ == "__main__":
        
##     full_sweep(SpecAn)        
##     run_offset()#Dont run this mid experiment, idiot...
##     SIH.free_run_plot_window('Y',full_span = 'Y')

##     times = np.array([0.02,0.01,0.009,0.008,0.007,0.006,0.005,0.004,0.003,0.002,0.001])
##     powers= np
##     frequency = 2.31*GHz
##     for loopy in range(len(times)):
##         var1 = times[loopy]
##         var2 = powers
##         burn_sequence(var1, frequency, var2)
##         frequency += 5*MHz
##         sleep(1)
## 
## full_sweep(SpecAn)
##     burn_n_sit(0.2*s,0.5*GHz,0,hl = 'high')


#========= Spin Polarize Stuff =============
    stop_f = 1*GHz
##     full_offset(SpecAn, stop_f) #Run once
##     SIH.free_run_plot_window('Y',full_span = 'Y')

    full_sweep(SpecAn)
    spin_pump_seq(2.43*GHz,800,record = "False")
    x,y=burn_sequence(0.2,1.200*GHz,-15,hl = 'high')
    SIH.free_run_plot_window('Y',full_span = 'Y')
##     
##     HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
##     full_sweep(SpecAn)


##     SpecAn.write('LG 2')
##     filepath = create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0)
##     pb.Sequence([(['ch5'], 0.5*s)] + [(['ch2','ch5','ch4'], 100*ms)] + [(['ch2','ch5'], 100*ms)], loop=False)
##     x,y,p=record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = 0)
##     sleep(0.1)
##  
##     SpecAn.write('LG 1')
##     SpecAn.write('FB ' + str(stop_f))
##     filepath = create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0, filename = 'zoom')
##     pb.Sequence([(['ch5'], 0.5*s)] + [(['ch2','ch5','ch4'], 100*ms)] + [(['ch2','ch5'], 100*ms)], loop=False)
##     x,y,p=record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = 0)

##     sleep(0.1)
##     SpecAn.write('LG 2')
##     full_sweep(SpecAn)


    



