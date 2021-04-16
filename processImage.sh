#!/bin/bash

# *************************************************** 
#   This is a script for
#   a Digital ePaper Photo Frame using Raspberry Pi B+, Waveshare ePaper Display and ProtoStax enclosure
#   --> https://www.waveshare.com/product/modules/oleds-lcds/e-paper/2.7inch-e-paper-hat-b.htm
#   --> https://www.protostax.com/products/protostax-for-raspberry-pi-b
#
#   It uses ImageMagick to tranform a regular image file into a tri-color version
#   suitable for displaying on a 264x176 Waveshare ePaper Display, resizing the image,
#   using a limited (3-color) palette and Floyd Steinberg Dithering, and splitting up
#   the image into black and white and black and red components for the ePaper library to display
#
#   The python code in main.py already does this logic in python using the Python Wand library, and
#   does so in-memory
#   Use this script if you want to prepare the images separately or otherwise play with your images
#   using ImageMagick.
#   This file is here as reference for the conversion process and commands to use. 
 
#   Written by Sridhar Rajagopal for ProtoStax.
#   BSD license. All text above must be included in any redistribution
# *

# Create palette with red, white and black colors
convert xc:red xc:white xc:black +append palette.gif

# Resize input file into size suitable for ePaper Display - 264x176
# Converting to BMP.
# Note, if working with JPG, it is a lossy
# format and subsequently remapping and working with it results
# in the color palette getting overwritten - we just convert to BMP
# and work with that instead
convert $1 -resize 264x176^ -gravity center -extent 264x176 resized.bmp

# Remap the resized image into the colors of the palette using
# Floyd Steinberg dithering (default)
# Resulting image will have only 3 colors - red, white and black
convert resized.bmp -remap palette.gif result.bmp


# Replace all the red pixels with white - this
# isolates the white and black pixels - i.e the "black"
# part of image to be rendered on the ePaper Display
convert -fill white -opaque red result.bmp result_black.bmp 

# Similarly, Replace all the black pixels with white - this
# isolates the white and red pixels - i.e the "red"
# part of image to be rendered on the ePaper Display
convert -fill white -opaque black result.bmp result_red.bmp

# If you want to further convert the white and red image above
# into a white and black image, use the following:
# This step is not needed really
convert -fill black -opaque red result_red.bmp result_red_to_black.bmp

# XXX : TODO
# Combine all of these steps into one command without creating intermediate
# temp files
# If you want to contribute, please submit a pull request! :-) 
