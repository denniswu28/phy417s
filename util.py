import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import astropy
import astropy.units as u
import scipy
import scipy.constants as cnst
from scipy.signal import savgol_filter 
import glob
import re

def freq2vel(freq, units = False):
    freq_0 = 1420.405751768
    vel = (freq_0-freq)/freq_0*cnst.c/1000
    if units:
        return vel*u.kilometer/u.second
    else:
        return vel

def power2temp(power, units = False):
    if units:
        return power*90*u.K
    else:
        return power*90

def volt2power(volt, units = False):
    if units:
        return np.power(volt,2)/50*u.power
    else:
        return np.power(volt,2)/50
    
def volt2temp(volt, units = False):
    if units:
        return power2temp(volt2power(volt), units = True)
    else:
        return power2temp(volt2power(volt))

def read_freq(file_path):
    df = pd.read_csv(file_path, sep = '\t', skiprows = 1, names = ['Frequency', 'Amplitude'])
    return df
    
def find_bg_signal(df, graph=False):
    if graph:
        sns.histplot(data =df, x= 'Amplitude', bins = 100, kde= True)
    hist, bin_edges = np.histogram(df['Amplitude'], bins=200, density = False)
    eval_points = np.linspace(np.min(bin_edges), np.max(bin_edges), num = 200)
    kde_max = eval_points[np.argmax(scipy.stats.gaussian_kde(df['Amplitude']).pdf(eval_points))]
    # hist_max = (bin_edges[np.argmax(hist)] + bin_edges[np.argmax(hist)+1] )/2
    return kde_max

def remove_width(arr, peaks, width):
    n = arr.size
    for peak in peaks:
        arr[peak] = np.nan
        for i in range(1,(width-1)//2):
            if peak - i > 0:
                arr[peak-i] = np.nan
            if peak + i < n:
                arr[peak+i] = np.nan
    return pd.Series(arr).interpolate(method='linear', limit_direction='both').to_numpy()


def remove_spike(df, graph=False):
    bg = find_bg_signal(df)
    std = np.std(df['Amplitude'])
    noise_std = np.std(df['Amplitude'][df['Amplitude']<bg])
    
    df['clipped'] = df['Amplitude'][df['Amplitude'] < bg+3.5*std]
    df['clipped'] = pd.Series(df['clipped']).interpolate(method='linear', limit_direction='both').to_numpy()
    peaks = scipy.signal.find_peaks_cwt(df['clipped'], np.arange(1,5), min_snr=2, min_length=0)
    
    df['unpeaked'] = df['clipped']
    df['unpeaked'] = remove_width(df['unpeaked'], peaks, 7)
    
    if graph:
        sns.histplot(data =df, x= 'clipped', bins = 100, kde= True)
        # plt.clf()
    
    # plt.plot(df['Frequency'],df['Amplitude']) 
    # plt.plot(df['Frequency'],df['filtered'])
    # plt.plot(df['Frequency'],df['unpeaked'])

    return df