# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 17:46:19 2018
@author: capland
modified by Derek Bean
"""

import numpy as np
import h5py
import os
import tables
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


class SfmovTools:
    """
    This class is a collection of tools that can be used to convert sfmov binary files from FLIR IR cameras
    into hdf5 datasets with defined compression.

    TODO: add functionality to get the data from the pod files and the extra data from the inc files
    TODO: Finish writing tests especially ones that check to make sure the data is converted correctly
    """
    def __init__(self, opendir, savedir, fname):
        """
        Initialize all of the parameters that are needed for the file conversion

        Inputs:
            opendir: Location of the files to be opened
            savedir: Location to save the converted files in
            fname:   Name of the file to be converted that has been stripped of file extensions

        Outputs:
            NONE
        """
        self.opendir = self.path_handling(opendir)
        self.savedir = self.path_handling(savedir)
        self.file = os.path.splitext(os.path.basename(fname))[0]
        self.frame_rate = float
        self.int_time = float
        self.data = float
        self.dimensions = {'height': int, 'width': int}
        self.number_of_frames = int
        self.dropped_frames = int
        self.length_DATA = 75  # Length of the data in each row with the return character
        self.camera_name = str()

    @staticmethod
    def path_handling(path):
        """ TODO: Need to remove and replace function with os package for path handling across operating systems"""
        path.replace('\\', '/')
        if path[0] == '/':
            path = '/' + path
        return path

    @staticmethod
    def extensions():
        """Returns the file extension that are used in the class"""
        return {'sfmov': '.sfmov', 'inc': '.inc', 'hdf5': '.hdf5'}
    


    def open_file(self, extension):
        """ Open and return a file object based on the input path"""
        return open(os.path.join(self.opendir, self.file + self.extensions()[extension]),
                    'r+b')

    def scrape_inc(self):
        """
        Scrape the integration time and frame rate from the .inc file and store
        them as object variables

        Inputs:
            none outside of class instance methods

        Outputs:
            frame_rate:  (float) camera's set frame rate
            int_time:    (float) camera's set integration time
            camera_name: (string) camera's name
        """


        with self.open_file('inc') as file:
            file_lines = file.readlines()
            inc_data = {x[0]: x[1:] for x in [s.split(b' ') for s in file_lines]}
            
            get_index = lambda key_list, byte_key: [x for x in key_list if byte_key in x].pop()
            
            integration_key = get_index(inc_data.keys(), b'ITime')
            frame_rate_key =  get_index(inc_data.keys(), b'FRate')
            camera_name_key = get_index(inc_data.keys(), b'CameraName')
            self.int_time = float(inc_data[integration_key][0])
            self.frame_rate = float(inc_data[frame_rate_key][0])
            self.camera_name = inc_data[camera_name_key][0].strip(b'\n').strip(b'\r')
        return self.frame_rate, self.int_time, self.camera_name

    def scrape_sfmov(self):
        """
        Read the image data from the sfmov binary file

        Take the data from the sfmov files where it is stored as encoded binary and gather
        the data and frame information. First the frame dimensions and number of frames are taken
        from the file and used to shape the data array. The data is then scraped from the file and
        stored in a numpy array. If the file is too large for the system memory the data is read in
        on a frame by frame basis and stored on disk instead of memeory.

        Inputs:
            Class instance methods

        Outputs:
            data:       (numpy array) image data shaped in the format (frame_number, height, width)
            TODO: change dimensions to a dict called info with the dimensions number of frames and dropped frames
        """
        with self.open_file('sfmov') as file:
            # content will contain the data in the file header
            content = {}
            # Iterate through the file line by line and store the data in the content dictionary
            # until the Data section of the file starts
            for row in file:
                row_contents = row.strip(b'\n').strip(b'\r').split(b' ')
                content[row_contents[0]] = row_contents[1:]
                if b'DATA' in row:
                    break
            # record the dimensions of the frame
            self.dimensions['width'] = int(content.pop(b'xPixls')[0])
            self.dimensions['height'] = int(content.pop(b'yPixls')[0])
            # frames_claimed is the number of frames the camera thinks is in the data provided no frames are dropped
            frames_claimed = int(content.pop(b'NumDPs')[0])
            # Starting after the data header read the data into a numpy array and then reshape it based on the
            # frame dimensions from the file header
            try:
                self.data = np.fromfile(file, dtype=np.uint16)
                self.data = np.reshape(self.data, (-1, self.dimensions['height'], self.dimensions['width']))
            except:
                # If the file is to big to fit in memory read the data in frame by frame using a np.memmap
                # format. This uses disk space to store the data and takes quite a bit longer than the previous method
                self.data = np.memmap('temp_sfmov_data',
                                      dtype=np.uint16, mode='w+',
                                      shape = (frames_claimed, self.dimensions['height'], self.dimensions['width']))
                frame_pixels = self.dimensions['height']*self.dimensions['width']
                for i in range(frames_claimed):
                    temp_array = np.fromfile(file, dtype=np.uint16, count=frame_pixels)
                    temp_array = np.reshape(temp_array, (self.dimensions['height'], self.dimensions['width']))
                    self.data[i, :, :] = temp_array
                # remove the temporary frame data
                os.remove('temp_sfmov_data')

            self.number_of_frames = self.data.shape[0]  # Actual number of frames
            self.dropped_frames = frames_claimed - self.number_of_frames
        return self.data, self.dimensions, self.number_of_frames, self.dropped_frames

    def convert(self, compression_factor=5):
        """Create a hdf5 binary database file of the converted data. Accepts a compression factor from 0 to 9
        to define the amount of compression of the output file"""
        self.scrape_sfmov()
        self.scrape_inc()
        try:
            with h5py.File(os.path.join(self.savedir, self.file +
                                        self.extensions()['hdf5']),
                           'w-',) as file:
                file.create_dataset('data', data=self.data, compression='gzip',
                                    compression_opts=compression_factor)
                file.create_dataset('number_of_frames',
                                    data=self.number_of_frames)
                file.create_dataset('width', data=self.dimensions['width'])
                file.create_dataset('height', data=self.dimensions['height'])
                file.create_dataset('dropped_frames', data=self.dropped_frames)
                file.create_dataset('frame_rate', data=self.frame_rate)
                file.create_dataset('int_time', data=self.int_time)
        except OSError:
            raise OSError('The file already exists please choose'+
                          'a different one or delete the file')
        return self.data

    @staticmethod
    def view(filename):
        """
            Create an interactive matplotlib window for viewing the videos.
            The frames can be scrolled through using the scroll wheel for
            individual frames and the mean counts slider for large adjustments.

            Inputs:
                filename: location of the hdf5 file to be viewed
            Outputs:
                a matplotlib window that allows scrubbing through videos
        """
        class VideoViewer(object):
            """
                A class that creates the plot window and updates based on user
                inputs. This class is setup to show each image on a central
                frame and then provide alternative data and frame selection
                in the plot below it.
            """
            def __init__(self, ax1, ax2, X):
                # Set the class variables and format the plot windows
                self.ax1 = ax1
                self.ax2 = ax2
                self.ax2.set_ylabel('Mean Counts')
                self.ax2.set_xlabel('Frame Number')
                ax1.set_title('use scroll wheel to navigate images' +
                              'or click on the mean counts plot')
                self.X = X
                self.num_frames, _, _ = X.shape  # get the number of frames
                # initialize the frame slider over the top of the ax2 plot and
                # to have a range from 0 to the number of frames with no fill a
                # step of 1 and an integer display
                self.frameSlider = Slider(self.ax2.axes, '', 0,
                                          self.num_frames-1, valstep=1,
                                          valfmt='%i', fill=False)
                self.ind = 0  # set the start indes
                # Cacluate the mean counts for each frame
                self.meanCounts = np.mean(self.X, axis=(1, 2))
                # plot the first image
                self.im = ax1.imshow(self.X[self.ind])
                # plot the mean counts
                self.ax2.plot(self.meanCounts)
                # run the update function to show the plot
                self.update()

            def onscroll(self, event):
                """
                 Change the frame index based on the scroll wheel movement
                """
                if event.button == 'up':
                    self.ind = (self.ind + 1) % self.num_frames
                else:
                    self.ind = (self.ind - 1) % self.num_frames
                self.update()

            def ondrag(self, event):
                """
                Change the displayed frame number to the slider value
                """
                self.ind = int(self.frameSlider.val)
                self.update()

            def update(self):
                """
                Redraw the plot with the updated image number
                """
                self.im.set_data(self.X[self.ind])
                self.im.axes.figure.canvas.draw()
        # Initialize the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [4, 1]})
        # Load the data from the hdf5 file using pytables
        image_data = tables.open_file(filename, mode='r').root.data.read()
        # Create the video viewer object and pass the plot and the data
        viewer = VideoViewer(ax1, ax2, image_data)
        # Connect the scroll wheel and the frame slide
        fig.canvas.mpl_connect('scroll_event', viewer.onscroll)
        viewer.frameSlider.on_changed(viewer.ondrag)
