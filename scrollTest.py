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
import pylab


def viewvideo(filename):
       
    class IndexTracker(object):
        def __init__(self, ax1, ax2, data):
            self.ax1 = ax1
            self.ax2 = ax2
            self.ax2.set_ylabel('Mean Counts')
            self.ax2.set_xlabel('Frame Number')
            ax1.set_title('use scroll wheel to navigate images or click on the mean counts plot')
            self.data = data
            self.slices, _, _ = data.shape
            self.frameSlider = Slider(self.ax2.axes, '', 0, self.slices-1,
                                      valstep=1, valfmt='%i', fill=False)
            self.ind = 0
    #        self.sFrame = Slider(plt.axes([0.25, 0.1, 0.65, 0.03]),
    #                             'Frame Number', 0, self.slices, valinit=0)
            
            self.meanCounts = np.mean(self.data, axis=(1,2))
            self.im = ax1.matshow(self.data[self.ind], cmap='plasma', vmin=0, vmax=16384)
            self.ax2.plot(self.meanCounts)
            self.update()
    
        def onscroll(self, event):
    #        print("%s %s" % (event.button, event.step))
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.frameSlider.set_val(self.ind)
            self.update()
    
            
        def ondrag(self, event):
    #        print('Slider Value is %s' % self.frameSlider.val)
            self.ind = int(self.frameSlider.val)
            self.update()
    
        def update(self):
            self.im.set_data(self.data[self.ind])
    #        self.ax1.set_ylabel('Frame %s' % self.ind)
            self.im.axes.figure.canvas.draw()
    print('Viewing: %s' % filename)
    fig, (ax1, ax2)  = plt.subplots(2, 1, gridspec_kw = {'height_ratios':[4, 1]})
    data = tables.open_file(filename, mode='r').root.data.read()
    print('Frame Rate: %s' % tables.open_file(filename, mode='r').root.frame_rate.read())
    tracker = IndexTracker(ax1, ax2, data)
#    fig.canvas.mpl_connect('slider_event', tracker.ondrag)
    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    tracker.frameSlider.on_changed(tracker.ondrag)
    plt.show(block=True)



if __name__ == "__main__":
    fileDirectory = "D:\\Ignition_12_19_2018\\"
    os.chdir(fileDirectory)
    fileList = glob("*.hdf5")
    [print(idx, val) for idx, val in enumerate(fileList)]
    viewer = viewvideo(fileList[9])