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
        #a, b = np.split(image, 2, axis=1)
    #return np.asarray(a), np.asarray(b)
    return np.asarray(image)


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
    print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
    print(" The button you used were: %s %s" % (eclick.button, erelease.button))


def line_select_callback(eclick, erelease):
    click[:] = eclick.xdata, eclick.ydata
    release[:] = erelease.xdata, erelease.ydata
    print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata))
    print(" The button you used were: %s %s" % (eclick.button, erelease.button))


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
    args = parser.parse_args()

    if args.load:
        # TO DO parametrize the load for more files ======

        # print(args.file.split('/')[0])
        # print(fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-left.npy'))
        # print(fnmatch.filter(os.listdir('.'), '*' + args.file.split('/')[1] + '-right.npy'))
        # javabridge.start_vm(class_path=bf.JARS, max_heap_size='8G')
        # r = read_first(args.file)
        # javabridge.kill_vm()
        # # Select region in the function
        # from matplotlib import pyplot as plt
        # print("\n      click  -->  release")
        # fig = plt.figure()
        # ax = fig.add_subplot(111)
        # ax.imshow(r)
        # # drawtype is 'box' or 'line' or 'none'
        # toggle_selector.RS = widgets.RectangleSelector(ax, line_select_callback,
        #                                drawtype='box', useblit=True,
        #                                button=[1, 3],  # don't use middle button
        #                                minspanx=5, minspany=5,
        #                                spancoords='pixels',
        #                                interactive=True)
        # plt.connect('key_press_event', toggle_selector)
        # plt.show()

        right = np.load(args.file + '-right.npy')
        left = np.load(args.file + '-left.npy')
        #return 0
    else:
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
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.imshow(left[0])
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.imshow(right[0])
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.imshow(np.concatenate((left[0], right[0]), axis=1))
    plt.show()
    print(left.shape, right.shape, len(left))

    # Select region in the function
    print("\n      click  -->  release")
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.imshow(right[0])
    # drawtype is 'box' or 'line' or 'none'
    toggle_selector.RS = widgets.RectangleSelector(ax, line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels',
                                       interactive=True)
    plt.connect('key_press_event', toggle_selector)
    plt.show()

    # Crop according to selected region and average region
    lcrop, rcrop = [], []
    l_avg, r_avg = [], []
    for i in range(0, len(left)-1):
        rcrop.append(crop(right[i], int(click[0]), int(click[1]), int(release[0]), int(release[1])))
        lcrop.append(crop(left[i], int(click[0]), int(click[1]), int(release[0]), int(release[1])))
        l_avg.append(np.average(left[i]))
        r_avg.append(np.average(right[i]))

    rcrop, lcrop = np.asarray(rcrop), np.asarray(lcrop)
    np_subtr = np.subtract(lcrop[12], rcrop[12])
    np_subtr2 = np.subtract(rcrop[12], lcrop[12])
    # Show random cropped image
    fig = plt.figure()
    ax1 = fig.add_subplot(3, 1, 1)
    ax1.imshow(np.concatenate((lcrop[12], rcrop[12], np_subtr, np_subtr2), axis=1))

    # Plot the averages into the graphs
    ax2 = fig.add_subplot(3, 1, 2)
    ax2.plot(l_avg, label='Astrocytes')
    ax2.legend()
    ax3 = fig.add_subplot(3, 1, 3)
    ax3.plot(r_avg, label='Neurons')
    ax3.legend()
    plt.show()


# Global variables
click = [None, None]
release = [None, None]


if __name__ == '__main__':
    sys.exit(main())
