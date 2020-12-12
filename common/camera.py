# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage
import common.twitter_avalon as twitter

import os
import glob
import datetime

# fswebcam --list-controls
brightness_min = 30
brightness_max = 255

# path to brightness test capture
test_capture = path.to('data/_test_capture.jpeg')
brightness_save = path.to('data/camera_brightness.save')

# full path to truetype file used for annotations
overlay_font = '/usr/local/share/fonts/SpaceMono-Regular.ttf'

def get_last_photo():
    dir = path.to('data/capture/')
    files = glob.glob(dir + '*')

    return max(files, key = os.path.getctime)

def take_photo():
    # heat up the camera
    startup()

    # get correct brightness
    camera_brightness = max(brightness_min, load_brightness() - 20)

    while camera_brightness <= brightness_max:
        mean = get_mean_brightness(camera_brightness)
        if mean >= 20.0:
            break

        camera_brightness += 10

    if camera_brightness > brightness_max:
        camera_brightness = brightness_max

    save_brightness(camera_brightness)
    log.info('using brightness {} to capture a photo.'.format(camera_brightness))

    # capture full photo
    filedate = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
    capture = path.to('data/capture/capture_{}.jpeg'.format(filedate))

    if os.path.isfile(capture):
        return

    # take photo: skip first five frames, create photo from another ten frames.
    result = os.system('fswebcam -q -S 5 -F 15 --set Brightness={} --set Contrast=5 --no-banner --rotate 180 -r 1280x720 --jpeg 80 "{}"'.format(camera_brightness, capture))
    if result == 0:
        # add current wather
        weather_first = '{} °c'.format(storage.get_netatmo_value('temp_out'))
        weather_second = '{} mb'.format(storage.get_netatmo_value('pressure'))

        os.system('convert -font {} -fill white -pointsize 24 -gravity SouthWest -draw \'text 60,40 "{}"\' -draw \'text 60,10 "{}"\' {} {}'.format(overlay_font, weather_first, weather_second, capture, capture))

        # add current time
        now = datetime.datetime.now()
        time_hour = '{:02d}'.format(now.hour)
        time_minute = '{:02d}'.format(now.minute)

        os.system('convert -font {} -fill white -pointsize 50 -gravity SouthWest -draw \'text 240,4 "{}h{}"\' {} {}'.format(overlay_font, time_hour, time_minute, capture, capture))

        log.info('image captured and saved to {}'.format(capture))
        return capture
    else:
        log.error('failed to capture image: {}'.format(result))
        return

def make_video():
    filedate = datetime.datetime.today().strftime("%Y_%m_%d")
    captures = path.to('data/capture/capture_{}*.jpeg'.format(filedate))
    video = path.to('data/video/video_{}.mp4'.format(filedate))

    result = os.system('ffmpeg -r 10 -pattern_type glob -i "{}" -c:v libx264 {}'.format(captures, video))
    if result == 0:
        log.info('video created and saved to {}'.format(video))
        return video
    else:
        log.error('failed to create video: {}'.format(result))
        return

def startup():
    if os.path.isfile(test_capture):
        os.remove(test_capture)

    os.system('fswebcam -q -D 3 -S 1 -F 5 --set Brightness={} --set Contrast=5 --no-banner -r 1280x720 --jpeg 80 "{}"'.format(brightness_min, test_capture))

    if not os.path.isfile(test_capture):
        log.error('startup(): unable to start the camera.')

        if not storage.is_locked('camera_startup'):
            twitter.tweet('❌ unable to start the camera. do something!')
            storage.lock('camera_startup', 2*60*60)


def get_mean_brightness(camera_brightness):
    if os.path.isfile(test_capture):
        os.remove(test_capture)

    # take a photo: skip first five frames, create photo from two another frames.
    result = os.system('fswebcam -q -S 5 -F 15 --set Brightness={} --set Contrast=5 --no-banner -r 1280x720 --jpeg 80 "{}"'.format(camera_brightness, test_capture))
    if result == 0:
        # crop upper half (camera is upside down!)
        os.system('convert {} -crop 1280x360+0+0 {}'.format(test_capture, test_capture))

        # get mean brightness of the photo
        mean = os.popen('convert {} -colorspace Gray -format "%[fx:100*image.mean]" info: '.format(test_capture)).read().strip()

        log.info('brightness: {} → {}'.format(camera_brightness, mean))

        return float(mean)
    else:
        return -1.0

def save_brightness(brightness):
    file = open(brightness_save, 'w')
    file.write(str(brightness))
    file.close()

def load_brightness():
    if not os.path.exists(brightness_save):
        return 0

    file = open(brightness_save, 'r')
    brightness = int(file.read())
    file.close()

    return brightness
