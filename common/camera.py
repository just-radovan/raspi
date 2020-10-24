#!/usr/bin/python3.7

import path
import common.log as log

import os
import datetime

# fswebcam --list-controls
brightness_min = 30
brightness_max = 255

def get_mean_brightness(camera_brightness):
    test_image = path.to('data/capture/_test_capture.jpeg')

    if os.path.isfile(test_image):
        os.remove(test_image)

    result = os.system('fswebcam -q -S 5 -F 2 --set Brightness={} --set Contrast=0 --no-banner -r 160x120 --jpeg 80 "{}"'.format(camera_brightness, test_image))
    if result == 0:
        mean = os.system('convert {} -colorspace Gray -format "%[fx:100*image.mean]" info:'.format(test_image))
        return float(mean)
    else:
        return -1.0

def take_photo():
    camera_brightness = brightness_min

    while camera_brightness <= brightness_max:
        mean = get_mean_brightness(camera_brightness)
        if mean >= 20.0:
            break

        camera_brightness += 20

    if camera_brightness > brightness_max:
        camera_brightness = brightness_max


    log.info('using brightness {} to capture a photo.'.format(camera_brightness))

    filedate = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
    capture = path.to('data/capture/capture_{}.jpeg'.format(filedate))

    if os.path.isfile(capture):
        return

    result = os.system('fswebcam -q -S 5 -F 10 --set Brightness={} --set Contrast=0 --no-banner --rotate 180 -r 1280x720 --jpeg 80 "{}"'.format(camera_brightness, capture))
    if result == 0:
        log.info('image captured and saved to {}'.format(capture))
        return capture
    else:
        log.error('failed to capture image: {}'.format(result))
        return

def make_video():
    filedate = datetime.datetime.today().strftime("%Y_%m_%d")
    captures = path.to('data/capture/capture_{}*.jpeg'.format(filedate))
    video = path.to('data/video/video_{}.mp4'.format(filedate))

    result = os.system('ffmpeg -r 1 -pattern_type glob -i "{}" -c:v libx264 {}'.format(captures, video))
    if result == 0:
        log.info('video created and saved to {}'.format(video))
        return video
    else:
        log.error('failed to create video: {}'.format(result))
        return
