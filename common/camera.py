#!/usr/bin/python3.7

import path

import os

def take_photo():
    capture = path.to('data/capture.jpeg')

    os.remove(capture)
    result = os.system('fswebcam -q -D 2 -r 1280x720 --jpeg 80 "{}"'.format(capture))

    if result == 0:
        return capture
    else:
        return
