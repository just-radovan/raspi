#!/usr/bin/python3.7

import path

import os

def take_photo():
    capture = path.to('data/capture.jpeg')

    if os.path.isfile(capture):
        os.remove(capture)
    
    result = os.system('fswebcam -q -S 5 --no-banner --rotate 180 -r 1280x720 --jpeg 80 "{}"'.format(capture))
    if result == 0:
        return capture
    else:
        return
