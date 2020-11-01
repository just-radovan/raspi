#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage

import os
import math
import datetime
import shutil
from urllib import request

import pytz

url_base = 'http://portal.chmi.cz/files/portal/docs/meteo/rad/inca-cz/data'
url_postfix_rain = '/czrad-z_max3d/pacz2gmaps3.z_max3d.{}.0.png'
url_postfix_lightning = '/celdn/pacz2gmaps3.blesk.{}.png'

asset_terrain = path.to('assets/chmi_teren.png')
asset_cities = path.to('assets/chmi_sidla.png')
file_rain = path.to('data/chmi/rain.png')
file_lightning = path.to('data/chmi/lightning.png')

composite = path.to('data/chmi/composite.png')

def get_rain_intensity():
    download()
    create_composite()

    intensity = 0

    # todo: check for rain around kobylisy, return max. intensity in percent

    if os.path.isfile(composite):
        return [intensity, composite]

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
