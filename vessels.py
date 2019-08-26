#!/usr/bin/env python3

import argparse
import os
import sys
import tqdm
import xml.dom.minidom
import javabridge
import fnmatch
import numpy as np
import bioformats as bf
from scipy import signal
import matplotlib.widgets as widgets


# Read metadata and return metadata as object
def get_metadata(filename):
    metadata = bf.get_omexml_metadata(filename)
    return bf.omexml.OMEXML(metadata)


# Save metadata to pretty xml
def save_metadata(metadata, filename):
    data = xml.dom.minidom.parseString(metadata.to_xml())
    pretty_xml_as_string = data.toprettyxml()

    with open(filename + '-metadata.xml', 'w') as xmlfile:
        xmlfile.write(pretty_xml_as_string)


# Read first image
def read_first(filename):
    with bf.ImageReader(filename) as reader:
        image = reader.read(t=0, rescale=False)
        a, b = np.split(image, 2, axis=1)
    return np.asarray(a), np.asarray(b)


# Read the image
def read_images(filename):
    with bf.ImageReader(filename) as reader:
        # Shape of the data
        c_total = reader.rdr.getSizeC()
        x_total = reader.rdr.getSizeX()
        y_total = reader.rdr.getSizeY()
        z_total = reader.rdr.getSizeZ()
        t_total = reader.rdr.getSizeT()
        print('Number of color planes: {}'.format(c_total))
        print('Image Resolution: {}x{}'.format(x_total, y_total))
        print('Image depth: {}'.format(z_total))
        print('Number of frames in the image: {}'.format(t_total))

        # Hyperstacks not supported yet
        if 1 not in [z_total, t_total]:
            raise TypeError('Only 4D images are currently supported.')

        counter = t_total//10000
        file = filename.split('/')[1]
        # right, left = [], []
        frame = 0
        count = 1
        total = (t_total//counter)
        # TO DO redo the loading to not lose any frames
        while count <= counter:
            right, left = [], []
            for time in tqdm.tqdm(range((count-1)*frame, count*total), "Loading frames"):
                # Read image
                image = reader.read(t=time, rescale=False)
                a, b = np.split(image, 2, axis=1)
                left.append(a)
                right.append(b)
            np.save(str(count) + '-' + file + '-left.npy', np.asarray(left))
            np.save(str(count) + '-' + file + '-right.npy', np.asarray(right))
            frame = (t_total//counter)
            count += 1
        print('Images loaded')


def crop(array, x1, x2, y1, y2):
    width = abs(x2-x1)
    height = abs(y2-y1)
    return array[y1:y1 + height, x1:x1 + width]


# Select the Region and return Points
def line_select_callback_2(eclick, erelease):
    # eclick and erelease are the press and release events
    global x1, x2, y1, y2
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    print('({:f}, {:f}) --> ({:f}, {:f})'.format(x1, y1, x2, y2))
    print('The button you used were: {} {}'.format(eclick.button, erelease.button))


def line_select_callback(eclick, erelease):
    click[:] = eclick.xdata, eclick.ydata
    release[:] = erelease.xdata, erelease.ydata
    print('({:f}, {:f}) --> ({:f}, {:f})'.format(eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata))
    print('The button you used were: {} {}'.format(eclick.button, erelease.button))


def toggle_selector(event):
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print(' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print(' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)


def main() -> int:
    """Parameters"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='File to be processed', required=True)
    parser.add_argument('-l', '--load', help='Load frames from npy', action='store_true')
    parser.add_argument('-nl', '--neuronsleft', help='Neurons on left side. Default: right', action='store_true')
    args = parser.parse_args()

    if args.load:
        # Load files
        print('File name:')
        print(args.file.split('/')[0])
        print('Files to be loaded: ')
        print(fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-left.npy'))
        print(fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-right.npy'))
        # Load the files
        left_files = fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-left.npy')
        right_files = fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-right.npy')

        # Start javabridge
        javabridge.start_vm(class_path=bf.JARS, max_heap_size='8G')
        # Read the first file and make crop
        left, right = read_first(args.file)
        javabridge.kill_vm()

        if args.neuronsleft:
            first_image = left
        else:
            first_image = right
        # Select region in the function
        from matplotlib import pyplot as plt
        print("\n      click  -->  release")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.imshow(first_image)
        # Drawtype is 'box' or 'line' or 'none'
        toggle_selector.RS = widgets.RectangleSelector(ax, line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels',
                                       interactive=True)
        plt.connect('key_press_event', toggle_selector)
        plt.show()

        lcrop, rcrop = [], []
        l_avg, r_avg = [], []
        for i in tqdm.tqdm(range(len(left_files)), "Loading frames"):
            right, left = [], []
            right = np.load(right_files[i])
            left = np.load(left_files[i])
            for j in range(0, len(left)-1):
                lcrop, rcrop = [], []
                rcrop.append(crop(right[j], int(click[0]), int(click[1]), int(release[0]), int(release[1])))
                lcrop.append(crop(left[j], int(click[0]), int(click[1]), int(release[0]), int(release[1])))
                l_avg.append(np.average(left[j]))
                r_avg.append(np.average(right[j]))

        #right = np.load(args.file + '-right.npy')
        #left = np.load(args.file + '-left.npy')
        #return 0
    else:
        # Start the java bridge
        javabridge.start_vm(class_path=bf.JARS, max_heap_size='8G')
        # Get and save metadata
        m = get_metadata(args.file)
        save_metadata(m, args.file)
        # Read and save images as npy
        read_images(args.file)
        # Kill javabridge vm
        javabridge.kill_vm()
        print('Java VM killed')
        return 0

    from matplotlib import pyplot as plt

    # Plot the averages into the graphs
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax1.plot(l_avg, label='Astrocytes')
    ax1.legend()
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.plot(r_avg, label='Neurons')
    ax2.legend()
    plt.show()

    fig = plt.figure()
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.plot(l_avg, label='Astrocytes', color='blue')
    ax1.legend()
    detrend = signal.detrend(l_avg)
    ax2 = fig.add_subplot(4, 1, 2)
    ax2.plot(detrend, label='Detrend astrocytes', color='red')
    ax2.legend()
    ax3 = fig.add_subplot(4, 1, 3)
    ax3.plot(r_avg, label='Neurons', color='purple')
    ax3.legend()
    ax4 = fig.add_subplot(4, 1, 4)
    detrend2 = signal.detrend(r_avg)
    ax4.plot(detrend2, label='Detrend neurons', color='green')
    ax4.legend()
    plt.show()

# Global variables
click = [None, None]
release = [None, None]


if __name__ == '__main__':
    sys.exit(main())
