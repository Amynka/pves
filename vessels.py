#!/usr/bin/env python3

from PIL import Image
import numpy

# Read the Image
im = Image.open('exp.vsi')

# Show the Image
# im.show()

# Convert to numpy array
nim = numpy.array(im)

# Print shape of the array
print('Shape of numpy array: {}'.format(nim.shape))

# Print size
print('Size of numpy: {}'.format(nim.size))

# Print the array
print('Numpy array: {}'.format(nim))
