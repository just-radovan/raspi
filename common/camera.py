#!/usr/bin/python3.7

import path

import os
import datetime

def take_photo():
    filedate = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
    capture = path.to('data/capture/capture_{}.jpeg'.format(filedate))

    if os.path.isfile(capture):
        return

    result = os.system('fswebcam -q -S 5 -F 10 --set Brightness=50 --set Contrast=0 --no-banner --rotate 180 -r 1280x720 --jpeg 80 "{}"'.format(capture))
    if result == 0:
        return capture
    else:
        return

def make_video():
    filedate = datetime.datetime.today().strftime("%Y_%m_%d")
    captures = path.to('data/capture/capture_{}*.jpeg'.format(filedate))
    video = path.to('data/video/video_{}.mp4'.format(filedate))

    result = os.system('ffmpeg -i {} -c:v h264_omx -b:v 3000k -pass 1 -an -y -f mp4 /dev/null && ffmpeg -i {} -movflags +faststart -c:v h264_omx -b:v 3000k -ar 48000 -y {}'.format(captures, captures, video))
    if result == 0:
        os.remove(captures)

        return video
    else:
        return
