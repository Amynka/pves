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

        #metadata = get_metadata(filename)

        images = []
        for time in tqdm.tqdm(range(t_total), "Loading frames"):
            # Read image
            image = reader.read(t=time, rescale=False)
            images.append(image)
    return np.asarray(images)


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
        ims = np.load(args.file + '.npy')
    else:
        ims = read_images(args.file)
        np.save(args.file + '.npy', ims)
    print(ims.shape)
    print(ims[0])

    # Kill the javabridge vm
    javabridge.kill_vm()


if __name__ == '__main__':
    sys.exit(main())
