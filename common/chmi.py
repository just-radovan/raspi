#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage

import os
import math
import datetime
import shutil
import numpy
from urllib import request

import pytz

url_base = 'http://portal.chmi.cz/files/portal/docs/meteo/rad/inca-cz/data'
url_postfix_rain = '/czrad-z_max3d/pacz2gmaps3.z_max3d.{}.0.png'
url_postfix_lightning = '/celdn/pacz2gmaps3.blesk.{}.png'

asset_terrain = path.to('assets/chmi_teren.png')
asset_cities = path.to('assets/chmi_sidla.png')
file_rain = path.to('data/chmi/rain.png')
file_lightning = path.to('data/chmi/lightning.png')

file_rain_cutout = path.to('data/chmi/rain_cutout.png')

composite = path.to('data/chmi/composite.png')

location = [227, 152] # coordinates of kobylisy on file_rain, file_lightning, and composite.
watch = [32, 32] # size of the area to watch for rain; with location in the middle.

color_map = [ # color legend for chmi rain data
	[56, 0, 112], # 04 mm/hr
	[48, 0, 168], # 08
	[0, 0, 252], # 12
	[0, 108, 192], # 16
	[0, 160, 0], # 20
	[0, 188, 0], # 24
	[52, 216, 0], # 28
	[156, 220, 0], # 32
	[224, 220, 0], # 36
	[252, 176, 0], # 40
	[252, 132, 0], # 44
	[252, 88, 0], #48
	[252, 0, 0], # 52
	[160, 0, 0], # 56
	[252, 252, 252] # 60
]

def get_rain_intensity():
    download()
    create_composite()

    if not os.path.isfile(composite):
        return

    color_map_len = len(color_map)
    intensity = 0
    area = 0

    for x in range(watch[0]):
        for y in range(watch[1]):
            pixel = os.popen('convert {} -format "%[fx:int(255*p{{{x},{y}}}.r)],%[fx:int(255*p{{{x},{y}}}.g)],%[fx:int(255*p{{{x},{y}}}.b)]" info:-'.format(file_rain_cutout, x = x, y = y)).read().strip()
            colors = pixel.split(',')

            r = int(colors[0])
            g = int(colors[1])
            b = int(colors[2])

            for r in range(color_map_len):
                mmhr = (r + 1) * 4 # mm/hr

                color = color_map[r]
                if r < (color_map_len - 2):
                    color_next = color_map[r + 1]
                else:
                    color_next = None

                if color == [r, g, b]:
                    # matches map color
                    intensity = math.max(intensity, mmhr)
                    area += 1
                elif color_next and (((color[0] <= r <= color_next[0]) or (color[0] >= r >= color_next[0])) and ((color[1] <= g <= color_next[1]) or (color[1] >= g >= color_next[1])) and ((color[2] <= b <= color_next[2]) or (color[2] >= b >= color_next[2]))):
                    # is somewhere between two neighbouring map colors
                    intensity = math.max(intensity, mmhr)
                    area += 1

    area = math.floor((area / (watch[0] * watch[1])) * 100)

    log.info('radar data explored. rain: max {} mm/hr at {} % of the area.'.format(intensity, area))

    return [intensity, area, composite]

def create_composite():
    if os.path.isfile(composite):
        os.remove(composite)

    if not os.path.isfile(file_rain) or not os.path.isfile(file_lightning):
        log.error('can\'t create composite, files are not downloaded.')
        return

    os.system('convert {} {} -geometry +0+0 -composite {}'.format(asset_terrain, asset_cities, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_rain, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_lightning, composite))

    return composite

def download():
    timestamp = get_data_timestamp()

    url_rain = (url_base + url_postfix_rain).format(timestamp)
    url_lightning = (url_base + url_postfix_lightning).format(timestamp)

    download_image(url_rain, file_rain)
    download_image(url_lightning, file_lightning)

    if os.path.isfile(file_rain):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_rain, file_rain))

        x_rel = location[0] - math.floor(watch[0] / 2)
        y_rel = location[1] - math.floor(watch[1] / 2)
        os.system('convert {} -crop {}x{}+{}+{} +repage {}'.format(file_rain, watch[0], watch[1], x_rel, y_rel, file_rain_cutout))

    if os.path.isfile(file_lightning):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_lightning, file_lightning))

def download_image(url, path):
    if os.path.isfile(path):
        os.remove(path)

    try:
        with request.urlopen(url) as response, open(path, 'wb') as file:
            shutil.copyfileobj(response, file)
    except:
        log.error('failed to download {}'.format(url))
        return

    if os.path.isfile(path):
        log.info('downloaded {} to {}'.format(url, path))
    else:
        log.error('failed to download {}'.format(url))

def get_data_timestamp():
    now = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=10)

    yr = '{:04d}'.format(now.year)
    mo = '{:02d}'.format(now.month)
    dy = '{:02d}'.format(now.day)
    hr = '{:02d}'.format(now.hour)
    mn = '{:02d}'.format(math.floor(now.minute / 10) * 10)

    return '{}{}{}.{}{}'.format(yr, mo, dy, hr, mn)