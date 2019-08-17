#!/usr/bin/env python3

import argparse
import sys
import tqdm
import xml.dom.minidom
import javabridge
import numpy as np
import bioformats as bf


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

        right, left = [], []
        for time in tqdm.tqdm(range(t_total), "Loading frames"):
            # Read image
            image = reader.read(t=time, rescale=False)
            a, b = np.split(image, 2, axis=1)
            left.append(a)
            right.append(b)
            #images.append(image)
    #return np.asarray(images)
    return np.asarray(right), np.asarray(left)


def main() -> int:
    """Parameters"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='File to be processed', required=True)
    parser.add_argument('-l', '--load', help='Load frames from npy', action='store_true')
    args = parser.parse_args()

    # Start javabridge vm
    javabridge.start_vm(class_path=bf.JARS, max_heap_size='8G')

    # Get and save metadata
    m = get_metadata(args.file)
    save_metadata(m, args.file)
    if args.load:
        right = np.load(args.file + '-right.npy')
        left = np.load(args.file + '-left.npy')
    else:
        right, left = read_images(args.file)
        np.save(args.file + '-right.npy', right)
        np.save(args.file + '-left.npy', left)
        print(right.shape, left.shape)

    from matplotlib import pyplot as plt
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.imshow(left[0])
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.imshow(right[0])
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.imshow(np.concatenate((left[0],right[0]), axis=1))
    plt.show()

    # Kill javabridge vm
    javabridge.kill_vm()


if __name__ == '__main__':
    sys.exit(main())
