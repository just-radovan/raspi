#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage

import os
import math
import time
import datetime
import sqlite3
import shutil
import numpy
import pytz
from geopy import distance
from urllib import request

url_base = 'http://portal.chmi.cz/files/portal/docs/meteo/rad/inca-cz/data'
url_postfix_rain = '/czrad-z_max3d/pacz2gmaps3.z_max3d.{}.0.png'
url_postfix_lightning = '/celdn/pacz2gmaps3.blesk.{}.png'

asset_terrain = path.to('assets/chmi_teren.png')
asset_cities = path.to('assets/chmi_sidla.png')
file_rain = path.to('data/chmi/rain.png')
file_lightning = path.to('data/chmi/lightning.png')

file_rain_cutout = path.to('data/chmi/rain_cutout.png')

composite = path.to('data/chmi/composite.png')

watch = 20 # radius of the area to watch for rain

color_map = [ # color legend for chmi rain data
	(56, 0, 112), # 04 mm/hr
    (48, 0, 168), # 08
	(0, 0, 252), # 12
	(0, 108, 192), # 16
	(0, 160, 0), # 20
	(0, 188, 0), # 24
	(52, 216, 0), # 28
	(156, 220, 0), # 32
	(224, 220, 0), # 36
	(252, 176, 0), # 40
	(252, 132, 0), # 44
	(252, 88, 0), #48
	(252, 0, 0), # 52
	(160, 0, 0), # 56
	(252, 252, 252) # 60
]

def get_my_pixel(): # -> (x, y)
    # define avalon
    avalon_pixel = (226, 149) # it's x,y
    avalon_gps = (50.1352602954946, 14.448018107292) # it's lat,lng / north,east / y,x

    # get current location
    location = storage.get_location()
    latitude = location[0]
    longitude = location[1]

    # get distances between avalon and current location
    dst_ns = distance.distance(avalon_gps, (latitude, avalon_gps[1])).km
    dst_ew = distance.distance(avalon_gps, (avalon_gps[0], longitude)).km

    if avalon_gps[0] < latitude:
        dst_ns_dir = -1 # on image: to the top
    else:
        dst_ns_dir = +1 # on image: to the bottom

    if avalon_gps[1] < longitude:
        dst_ew_dir = +1 # on image: to the left
    else:
        dst_ew_dir = -1 # on image: to the right

    my_x = avalon_pixel[0] + (dst_ew * dst_ew_dir)
    my_y = avalon_pixel[1] + (dst_ns * dst_ns_dir)

    # check image boundaries
    if my_x < 0 or my_x > 595:
        my_x = avalon_pixel[0]

    if my_y < 0 or my_x > 376:
        my_y = avalon_pixel[1]

    # create my pixel
    my_pixel = (
        int(avalon_pixel[0] + (dst_ew * dst_ew_dir)),
        int(avalon_pixel[1] + (dst_ns * dst_ns_dir))
    )

    log.info('get_my_pixel(): current position: {},{} at {},{}'.format(int(dst_ew * dst_ew_dir), int(dst_ns * dst_ns_dir), my_pixel[0], my_pixel[1]))

    return my_pixel

def get_rain_intensity():
    download()
    create_composite()

    if not os.path.isfile(file_rain_cutout):
        log.error('get_rain_intensity(): rain cutout is missing. can\'t get rain intensity.')
        return

    location = get_my_pixel()
    watch_x = location[0] - watch
    watch_y = location[1] - watch

    color_map_len = len(color_map)
    intensity = 0
    distance = None
    area_watch = 0
    area_rain = 0

    # detect rain
    for x in range(watch * 2):
        for y in range(watch * 2):
            dst = math.sqrt(abs(x - watch) ** 2 + abs(y - watch) ** 2)
            if dst > watch: # make it circle
                continue

            area_watch += 1

            pixel = os.popen('convert {} -format "%[fx:int(255*p{{{x},{y}}}.r)],%[fx:int(255*p{{{x},{y}}}.g)],%[fx:int(255*p{{{x},{y}}}.b)]" info:-'.format(file_rain_cutout, x = x, y = y)).read().strip()
            colors = pixel.split(',')

            r = int(colors[0])
            g = int(colors[1])
            b = int(colors[2])

            for clr in range(color_map_len):
                color = color_map[clr]
                if clr < (color_map_len - 2):
                    color_next = color_map[clr + 1]
                else:
                    color_next = None

                if (color == [r, g, b]) or (color_next and (((color[0] <= r < color_next[0]) or (color[0] >= r > color_next[0])) and ((color[1] <= g < color_next[1]) or (color[1] >= g > color_next[1])) and ((color[2] <= b < color_next[2]) or (color[2] >= b > color_next[2])))):
                    # rain intensity
                    mmhr = (clr + 1) * 4 # mm/hr
                    intensity = max(intensity, mmhr)

                    # rain impacted area
                    area_rain += 1

                    # distance to avalon
                    if not distance:
                        distance = dst
                    else:
                        distance = min(distance, dst)

    area = math.floor((area_rain / area_watch) * 100)

    if distance:
        log.info('get_rain_intensity(): radar data explored. rain: max {} mm/hr at {} % of the area. closest rain: {:.1f} kms.'.format(intensity, area, distance))
    else:
        log.info('get_rain_intensity(): radar data explored. no rain detected.')

    # store data
    db = None
    try:
        db = sqlite3.connect(path.to('data/rain_history.sqlite'))
    except Error as e:
        log.error('get_rain_intensity(): unable to open rain database: {}'.format(e))
        return

    cursor = db.cursor()
    cursor.execute(
        'insert into rain ("timestamp", "intensity", "distance", "area") values (?, ?, ?, ?)',
        (int(time.time()), intensity, distance if distance else -1.0, area)
    )

    db.commit()
    db.close()

def create_composite(): # -> composite filename (string)
    if os.path.isfile(composite):
        os.remove(composite)

    if not os.path.isfile(file_rain) or not os.path.isfile(file_lightning):
        log.error('create_composite(): can\'t create composite, files are not downloaded.')
        return

    os.system('convert {} {} -geometry +0+0 -composite {}'.format(asset_terrain, asset_cities, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_rain, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_lightning, composite))

    location = get_my_pixel()
    x = location[0]
    y = location[1]
    cx = location[0] - watch
    cy = location[1] - watch

    os.system('convert {} -fill "rgba(0, 0, 0, 0.0)" -stroke "rgba(0, 0, 0, 0.8)" -strokewidth 2 -draw "circle {},{} {},{}" {}'.format(composite, x, y, cx, cy, composite))

    return composite

def download():
    timestamp = get_data_timestamp()

    url_rain = (url_base + url_postfix_rain).format(timestamp)
    url_lightning = (url_base + url_postfix_lightning).format(timestamp)

    download_image(url_rain, file_rain)
    download_image(url_lightning, file_lightning)


    if os.path.isfile(file_rain):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_rain, file_rain))

        location = get_my_pixel()
        watch_x = location[0] - watch
        watch_y = location[1] - watch
        os.system('convert {} -crop {}x{}+{}+{} +repage {}'.format(file_rain, (watch * 2), (watch * 2), watch_x, watch_y, file_rain_cutout))

    if os.path.isfile(file_lightning):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_lightning, file_lightning))

def download_image(url, path):
    if os.path.isfile(path):
        os.remove(path)

    try:
        with request.urlopen(url) as response, open(path, 'wb') as file:
            shutil.copyfileobj(response, file)
    except:
        log.error('download_image(): failed to download {}'.format(url))
        return

    if os.path.isfile(path):
        log.info('download_image(): downloaded {} to {}'.format(url, path))
    else:
        log.error('download_image(): failed to download {}'.format(url))

def get_data_timestamp(back = 15): # -> chmi image timestamp (string)
    now = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes = back)

    yr = '{:04d}'.format(now.year)
    mo = '{:02d}'.format(now.month)
    dy = '{:02d}'.format(now.day)
    hr = '{:02d}'.format(now.hour)
    mn = '{:02d}'.format(math.floor(now.minute / 10) * 10)

    return '{}{}{}.{}{}'.format(yr, mo, dy, hr, mn)
