# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 16:44:02 2019

@author: beande
"""

from nptdms import TdmsFile
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def butter_filter(data, n=3, wn=0.005):
    b, a = signal.butter(n, wn, output='ba', btype='lowpass')
    return signal.filtfilt(b, a, data)


def peakFinder(data, numPeaks, stepSize=0.001):
    peaks = []
    threshold = 1
    while len(peaks) < numPeaks:
        peaks = signal.find_peaks(data, prominence=threshold*data.max())[0]
        threshold -= stepSize
    return peaks

def distanceBetweenPeaks(data, samplingFreq):
    ignitionTime = findIgnition(data)
    lowerTime = findHeater(data) 
    return (ignitionTime - lowerTime) / samplingFreq, ignitionTime, lowerTime


def findIgnition(data):
    return peakFinder(np.diff(data), 1)[0]


def findHeater(data):
    return peakFinder(np.diff(data), 10)[0]

def formatTempData(data, tempColumn=0, timeColumn=1):
    temperatures = data[data.columns[tempColumn]].values
    time = data[data.columns[timeColumn]].values
    time = [t - time[0] for t in time]
    return pd.Series(data=temperatures, index=time)




if __name__ == "__main__":
    dataFilePath = "D:\\Ignition_02_07_2019\\test015_02072019.tdms"
    dataFile = open(dataFilePath, 'rb')
    samplingFreq = 1000
    data = TdmsFile(dataFile).as_dataframe(absolute_time=True)
    testSample = data[data.columns[1]][4000:]
    temperatureData = data[data.columns[-2:]].dropna()
    temperatureData = formatTempData(temperatureData)
    filteredData = butter_filter(testSample)
    duration, ignitionTime, lowerTime = distanceBetweenPeaks(filteredData, samplingFreq)
    
    ignitionTemperature = temperatureData[temperatureData.index[temperatureData.index.get_loc(ignitionTime/samplingFreq, method='nearest', tolerance=1)]]
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    
    ax1.plot([x/samplingFreq for x in list(range(len(filteredData)))],
              filteredData, label='Photodiode')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax2.set_ylabel('Temperature $^{\circ}C$')
    ax1.scatter(ignitionTime/samplingFreq, filteredData[ignitionTime], label='Ignition')
    ax1.scatter(lowerTime/samplingFreq, filteredData[lowerTime], label='Heater Set')
    temperatureData.plot(style='rx--', ax=ax2, label='Thermocouple')
    fig.legend(loc=0)
