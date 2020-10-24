#!/usr/bin/python3.7

import path

import os
import datetime

def take_photo():
    filedate = datetime.date.today().strftime("%Y_%m_%d_%H_%M")
    capture = path.to('data/capture/capture_{}.jpeg'.format(filedate))

    if os.path.isfile(capture):
        return

    result = os.system('fswebcam -q -S 5 --no-banner --rotate 180 -r 1280x720 --jpeg 80 "{}"'.format(capture))
    if result == 0:
        return capture
    else:
        return
