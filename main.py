#!/usr/bin/python
# -*- coding:utf-8 -*-

# *************************************************** 
#   This is a example program for
#   a Digital ePaper Photo Frame using Raspberry Pi B+, Waveshare ePaper Display and ProtoStax enclosure
#   --> https://www.waveshare.com/product/modules/oleds-lcds/e-paper/2.7inch-e-paper-hat-b.htm
#   --> https://www.protostax.com/products/protostax-for-raspberry-pi-b
#
#   It uses the python Wand library to tranform a regular image file into a tri-color version
#   suitable for displaying on a 264x176 Waveshare ePaper Display, resizing the image,
#   using a limited (3-color) palette and Floyd Steinberg Dithering, and splitting up
#   the image into black and white and black and red components for the ePaper library to display
 
#   Written by Sridhar Rajagopal for ProtoStax.
#   BSD license. All text above must be included in any redistribution
# *

import sys
if sys.version_info[0] < 3:
    raise Exception("Please use Python version 3+ (python3) to run this program!!")

sys.path.append(r'epd')
import os
import io

import signal
import epd2in7b
import epdconfig
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
import RPi.GPIO as GPIO

from wand.image import Image as WandImage


# This function takes as input a filename for an image
# It resizes the image into the dimensions supported by the ePaper Display
# It then remaps the image into a tri-color scheme using a palette (affinity)
# for remapping, and the Floyd Steinberg algorithm for dithering
# It then splits the image into two component parts:
# a white and black image (with the red pixels removed)
# a white and red image (with the black pixels removed)
# It then converts these into PIL Images and returns them
# The PIL Images can be used by the ePaper library to display
def getImagesToDisplay(filename):
    print(filename)
    red_image = None
    black_image = None
    try:
        with WandImage(filename=filename) as img:
            img.resize(264, 176)
            with WandImage() as palette:
                with WandImage(width = 1, height = 1, pseudo ="xc:red") as red:
                    palette.sequence.append(red)
                with WandImage(width = 1, height = 1, pseudo ="xc:black") as black:
                    palette.sequence.append(black)
                with WandImage(width = 1, height = 1, pseudo ="xc:white") as white:
                    palette.sequence.append(white)
                palette.concat()
                img.remap(affinity=palette, method='floyd_steinberg')
                
                red = img.clone()
                black = img.clone()
                red.opaque_paint(target='black', fill='white')
                # This is not nececessary - making the white and red image
                # white and black instead - left here FYI
                # red.opaque_paint(target='red', fill='black')
        
                black.opaque_paint(target='red', fill='white')
                
                red_image = Image.open(io.BytesIO(red.make_blob("bmp")))
                black_image = Image.open(io.BytesIO(black.make_blob("bmp")))
    except Exception as ex:
        print ('traceback.format_exc():\n%s',traceback.format_exc())

    return (red_image, black_image)


# Array for list of file names for images to display        
pics = []
# picture index for the current image being displayed from above array
pic_index = -1

# How long to sleep between images, in secconds
SLEEP_TIME = 30

# XXX : TODO -
# Update the latest list of images
# Handle additions and deletions to the images in the pics folder
# Hint - Set might be easier to work with
# Move the logic from main() into separate function and also
# add logic to deal with changes in the directory

# Main function
def main():
    global pics
    # Let's get all the images in the pics/ directory and store them in the pics array
    # XXX : TODO - move this out to a separate function, and handle changes in
    # directory - new files getting added and existing ones getting deleted
    print("Getting list of files (images) to display") 
    basepath = 'pics/'
    for entry in os.listdir(basepath):
        if os.path.isfile(os.path.join(basepath, entry)):
            print(entry)
            pics.append(basepath+entry)

    # We'll start with the first image in the array, if it exists
    if (len(pics) > 0):
        pic_index = 0
    else:
        print("No files! Nothing to display! We'll just show the default images")

    # Let's initialize the ePaper Display
    epd = epd2in7b.EPD()
    print("Clear...")
    epd.init()
    epd.Clear()
    
    # red.bmp and black.bmp are the default images, in case
    # the pics/ directory has no images
    # These images just have a message that tells the user to populate
    # the pics/ directory
    # Let's think about usability! :-)  
    HBlackimage = Image.open(os.path.join('black.bmp'))
    HRedimage = Image.open(os.path.join('red.bmp'))

    # We'll start looping over the images to display, endlessly,
    # until stopped by Ctrl C
    while True:
        # Display photos and images on e-Paper Display
        try:
            epd.init()
            print("Getting image to display...")
            # If pictures exist in the pics array, we use those
            # otherwise, we've already defaulted to the red.bmp and black.bmp
            # images earlier
            if (len(pics) > 0):
                # let's get the scaled, color mapped and dithered
                # red and black images to display on the ePaper display
                # for the current picture index
                (HRedimage, HBlackimage) = getImagesToDisplay(pics[pic_index])

            print("Rendering display...")
            if (HRedimage != None and HBlackimage != None):
                epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRedimage))
                time.sleep(2)
            
            epd.sleep()
            
        except Except as e:
            print ('traceback.format_exc():\n%s',traceback.format_exc())
            epdconfig.module_init()
            epdconfig.module_exit()
            exit()

        # Let's get the next picture in the array.
        # We'll cycle over when we hit the end of the array
        if (len(pics) > 0):
            pic_index = (pic_index+1)%len(pics)
            
        # Sleep for a configured time before waking up to get and display the
        # next image
        time.sleep(SLEEP_TIME)
 
            
        
# gracefully exit without a big exception message if possible
def ctrl_c_handler(signal, frame):
    print('Goodbye!')
    # To preserve the life of the ePaper display, it is best not to keep it powered up -
    # instead putting it to sleep when done displaying, or cutting off power to it altogether when
    # quitting. We'll also make sure to clear the screen when exiting. If you are powering down your
    # Raspberry Pi and storing it and the ePaper display, it is recommended
    # that the display be cleared prior to storage, to prevent any burn-in.
    # 
    # I have modified epdconfig.py to initialize SPI handle in module_init() (vs. at the global scope)
    # because slepe/module_exit closes the SPI handle, which wasn't getting initialized in module_init.
    # I've also added a module_sleep (which epd.sleep calls) which does not call GPIO.cleanup, and
    # made module_exit call both module_sleep and GPIO.cleanup
    epd = epd2in7b.EPD()
    print("Clearing screen before exiting ... Please wait!")
    epd.init()
    epd.Clear()
    epd.exit()
    exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)

if __name__ == '__main__':
    main()
