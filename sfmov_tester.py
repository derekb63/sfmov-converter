# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 10:20:13 2018

@author: beande
"""

'''

File for testing the sfmovconverter

'''
from sfmov_converter import SfmovTools as st
import os
from glob import glob
import matplotlib.pyplot as plt
import tables
from matplotlib.widgets import Button


def stripExtension(filename):
    try:
        return filename.split('.')[0]
    except AttributeError:
        return [stripExtension(name) for name in filename]

def plot_images(image_file):
    h5file = tables.open_file(image_file, mode='r')
    fig, ax = plt.subplots()
    l = plt.imshow(h5file.root.data.read()[100])
    title = ax.text(1, 1, 'Frame 1')
    
    class Index(object):
        '''
            Class that updates the y data in the plots based on the index. This 
            class controls the plot updates and index counting
        '''
        def __init__(self, image):
        # initialize the index for the tests
            self.idx = 0
            self.image = image
        def next(self, event):
        # Move forward unless the last index is reached then wrap back to zero
            self.idx += 1
            try: 
                self.update_data()
            except IndexError:
                self.idx = 0
                self.update_data()
         
        def prev(self, event):
        # Move backwards until zero is reached then stay at zero
            self.idx -= 1
            try:
                self.update_data()
            except IndexError:
                self.idx = 0
                self.update_data()
        
        def update_data(self):
        # update the data and the title for the plots
            # get the new data
            self.image.set_data(h5file.root.data.read()[self.idx])
            # rename the title
            title.set_text('Test {0}'.format(self.idx+1))
            # set the data for each matplotlib line
            plt.draw()
    
    # define the Index class as the callback object that is called when
    # one of the buttons is pressed
    callback = Index(l)
    # Set the locations of the buttons
    axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    
    # Setup the next button (location, text)
    bnext = Button(axnext, 'Next')

    # Set the function that is called when the button is clicked
    bnext.on_clicked(callback.next)
    
    # Setup the previos button (location, text)
    bprev = Button(axprev, 'Previous')
    # Set the function that is called when the button is clicked
    bprev.on_clicked(callback.prev)
    fig.subplots_adjust(bottom=0.2)
    plt.show()
  
    

if __name__ == "__main__":
    fileDirectory = "E:\\sfmovFilesForDan\\"
    fileName = 'smold_20181102-000000.sfmov'
    converter = st(fileDirectory, fileDirectory, fileName)
    converter.convert()
#    os.chdir(fileDirectory)
#    fileList = glob("*.hdf5")
#    plot_images(fileList[0])
    
#    for file in fileList:
#        testData = st(fileDirectory, fileDirectory, file)
#        testData.convert(0)
    
    