#!/usr/bin/env python3

import argparse
import numpy
import bioformats as bf
import javabridge as jb
from PIL import Image


# Print shape of the array
#print('Shape of numpy array: {}'.format(nim.shape))

# Print size
#print('Size of numpy: {}'.format(nim.size))

# Print the array
#print('Numpy array: {}'.format(nim))

# Read metadata and return metadata as object
def get_metadata(filename):
	metadata = bf.get_omexml_metadata(filename)
	#return bf.omexml.OMEXML(metadata)
	return metadata


def main() -> int:
	"""Parameters"""
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--file', help='File to be processed', required=True)
	args = parser.parse_args()

	# Start javabridge vm
	jb.start_vm(class_path=bf.JARS, max_heap_size='2G')
	# Print metadata
	print(get_metadata(args.file))


if __name__ == '__main__':
	exit(main())



