# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 11:02:49 2018

@author: beande
"""
import numpy as np
import matplotlib.pyplot as plt
import tables
import os
from glob import glob
from matplotlib.widgets import Slider




def viewvideo(filename):
    class IndexTracker(object):
            def __init__(self, ax1, ax2, data):
                self.ax1 = ax1
                self.ax2 = ax2
                self.ax2.set_ylabel('Mean Counts')
                self.ax2.set_xlabel('Frame Number')
                ax1.set_title('use scroll wheel to navigate images or click on the mean counts plot')
                self.data = data
                print(data.shape)
                self.slices, _, _ = data.shape
                self.frameSlider = Slider(self.ax2.axes, '', 0, self.slices-1,
                                          valstep=1, valfmt='%i', fill=False)
                self.ind = 0
                self.meanCounts = np.mean(self.data, axis=(1, 2))
                self.im = ax1.matshow(self.data[self.ind], cmap='plasma', vmin=0, vmax=16384)
                self.ax2.plot(self.meanCounts)
                self.update()
        
            def onscroll(self, event):
    
                if event.button == 'up':
                    self.ind = (self.ind + 1) % self.slices
                else:
                    self.ind = (self.ind - 1) % self.slices
                self.frameSlider.set_val(self.ind)
                self.update()
    
            def ondrag(self, event):
                self.ind = int(self.frameSlider.val)
                self.update()
    
            def update(self):
                self.im.set_data(self.data[self.ind])
                self.im.axes.figure.canvas.draw()
    print('Viewing: %s' % filename)
    fig, (ax1, ax2)  = plt.subplots(2, 1, gridspec_kw = {'height_ratios':[4, 1]})
    data = tables.open_file(filename, mode='r').root.data.read()
#    dataBackgroundImage = np.mean(data[5000:11404], axis=0)
#    data = np.subtract(data[11911:14000], dataBackgroundImage)
    print('Frame Rate: %s' % tables.open_file(filename, mode='r').root.frame_rate.read())
    tracker = IndexTracker(ax1, ax2, data)
    fig.canvas.mpl_connect('slider_event', tracker.ondrag)
    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    tracker.frameSlider.on_changed(tracker.ondrag)
    plt.show(block=True)


if __name__ == "__main__":
    fileDirectory = "E:\\sfmofFilesForDan"
    os.chdir(fileDirectory)
    fileList = glob("*.hdf5")
    [print(idx, val) for idx, val in enumerate(fileList)]
    viewer = viewvideo(fileList[0])
