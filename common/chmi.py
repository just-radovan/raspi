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
import seaborn
import pandas
from PIL import Image
from geopy import distance
from urllib import request
from pylab import savefig

url_base = 'http://portal.chmi.cz/files/portal/docs/meteo/rad/inca-cz/data'
url_postfix_rain = '/czrad-z_max3d/pacz2gmaps3.z_max3d.{}.0.png'
url_postfix_lightning = '/celdn/pacz2gmaps3.blesk.{}.png'

asset_terrain = path.to('assets/chmi_teren.png')
asset_cities = path.to('assets/chmi_sidla.png')
file_rain = path.to('data/chmi/rain.png')
file_lightning = path.to('data/chmi/lightning.png')

composite_size = (595, 376) # x, y
composite = path.to('data/chmi/composite.png')
composite_avalon = path.to('data/chmi/composite_avalon.png')
composite_prague = path.to('data/chmi/composite_prague.png')
composite_pilsen = path.to('data/chmi/composite_pilsen.png')
composite_domazlice = path.to('data/chmi/composite_domazlice.png')

heatmap_file = path.to('data/chmi/heatmap.png')
heatmap_composite = path.to('data/chmi/heatmap_composite.png')

avalon_pixel = (226, 149) # it's x,y for avalon

avalon_gps = (50.1352602954946, 14.448018107292) # it's lat,lng / north,east / y,x
avalon_radius = 20 # radius of the area to watch for rain

prague_gps = (50.0789384, 14.4605103) # it's lat,lng / north,east / y,x
prague_radius = 15 # radius of the area to watch for rain

pilsen_gps = (49.743286, 13.373704) # it's lat,lng / north,east / y,x
pilsen_radius = 7 # radius of the area to watch for rain

domazlice_gps = (49.441526, 12.925853) # it's lat,lng / north,east / y,x
domazlice_radius = 4 # radius of the area to watch for rain

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
	(252, 88, 0), # 48
	(252, 0, 0), # 52
	(160, 0, 0), # 56
	(252, 252, 252) # 60
]

def get_week_rain_info(): # → path to heatmap composite file
    # load rain maps from last 7 days
    since = datetime.datetime.timestamp(datetime.datetime.now() - datetime.timedelta(days = 7))
    entries = load_rain_maps(since)

    log.info('get_week_rain_info(): loaded {} maps.'.format(len(entries)))

    # sum maps
    map_x = composite_size[0]
    map_y = composite_size[1]
    map = numpy.zeros(shape = (map_x, map_y))
    
    for entry in entries:
        map = numpy.add(map, entry[1])

    # normalize maps for 0..1
    map *= 1.0 / map.max() # maybe numpy.amax(array) will work instead of map.max()

    # create heat map
    data_frame = pandas.DataFrame(map)
    data_frame = data_frame.transpose()

    palette = seaborn.color_palette('rocket_r', as_cmap = True)
    heatmap = seaborn.heatmap(data_frame, vmin = 0, vmax = 1, cmap = palette, square = True, xticklabels = False, yticklabels = False, cbar = False)

    if os.path.isfile(heatmap_file):
        os.remove(heatmap_file)

    fig = heatmap.get_figure()
    fig.savefig(heatmap_file, dpi = 400)

    # crop & resize the heatmap
    if not os.path.isfile(heatmap_file):
        return

    os.system('convert {} -crop 1982x1252+320+343 +repage {}'.format(heatmap_file, heatmap_file))
    os.system('convert {} -resize {}x{}! {}'.format(heatmap_file, map_x, map_y, heatmap_file))

    # put map under heatmap
    os.system('convert {} -alpha set -background none -channel A -evaluate multiply 0.5 +channel {}'.format(heatmap_file, heatmap_file))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(asset_terrain, asset_cities, heatmap_composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(heatmap_composite, heatmap_file, heatmap_composite))
    os.system('convert {} -crop 500x290+49+37 +repage {}'.format(heatmap_composite, heatmap_composite))

    return heatmap_composite

def get_avalon_rain_info(when = None):
    return get_rain_info(when, get_avalon_pixel(), avalon_radius)

def get_prague_rain_info(when = None):
    return get_rain_info(when, get_prague_pixel(), prague_radius, True)

def get_pilsen_rain_info(when = None):
    return get_rain_info(when, get_pilsen_pixel(), pilsen_radius, True)

def get_domazlice_rain_info(when = None):
    return get_rain_info(when, get_domazlice_pixel(), domazlice_radius, True)

def get_rain_info(when, pixel, radius, distance_to_radius = False): # → (timestamp, intensity, area, area outside, distance)
    data = load_rain_map(when)

    if data is None: 
        return None

    timestamp = data[0]
    map = data[1]
    delta = int((time.time() - timestamp) / 60) # minutes
    
    area_watch = 0.0
    area_rain = 0.0
    perimeter_watch = 0.0
    perimeter_rain = 0.0
    intensity = 0
    distance = -1.0

    # detect rain in double the radius
    # (to see if there is rain outside the watched area)
    for x in range(radius * 4):
        for y in range(radius * 4):
            dx = x - (radius * 2) # [-x, +x]
            dy = y - (radius * 2) # [-y, +y]

            loc_x = pixel[0] + dx
            loc_y = pixel[1] + dy

            if not (0 <= loc_x < composite_size[0]) or not (0 <= loc_y < composite_size[1]):
                continue # we're outside of the map

            dst = math.sqrt(abs(dx) ** 2 + abs(dy) ** 2)

            if dst <= (radius * 2):
                map_intensity = map[loc_x, loc_y]

                if dst <= radius:
                    area_watch += 1
                    if map_intensity > 0:
                        area_rain += 1
                        intensity = max(intensity, map_intensity)
                else:
                    perimeter_watch += 1
                    if map_intensity > 0:
                        perimeter_rain += 1

                # store distance to watched area
                if map_intensity > 0:
                    if distance_to_radius:
                        dst_to_watch = max(0, dst - radius)
                    else:
                        dst_to_watch = dst

                    if distance < 0:
                        distance = dst_to_watch
                    else:
                        distance = min(distance, dst_to_watch)

    area = (area_rain / area_watch) * 100
    perimeter = (perimeter_rain / perimeter_watch) * 100

    if distance >= 0:
        log.info('get_rain_intensity(): @+{}m {}×{}: max {:.0f} mm/hr at {:.3f} % // perimeter: {:.3f} %, {:.1f} kms.'.format(delta, pixel[0], pixel[1], intensity, area, perimeter, distance))
    else:
        log.info('get_rain_intensity(): @+{}m {}×{}: no rain detected'.format(delta, pixel[0], pixel[1]))
        if perimeter > 0:
            log.warning('get_rain_intensity(): @+{}m {}×{}: no distance, but there\'s something out there: {:.2f} %!'.format(delta, pixel[0], pixel[1], perimeter))

    return (timestamp, intensity, area, perimeter, distance)

def get_avalon_pixel(): # -> (x, y)
    location = storage.get_location()

    return get_pixel(location[0], location[1])

def get_prague_pixel(): # -> (x, y)
    return get_pixel(prague_gps[0], prague_gps[1])

def get_pilsen_pixel(): # -> (x, y)
    return get_pixel(pilsen_gps[0], pilsen_gps[1])

def get_domazlice_pixel(): # -> (x, y)
    return get_pixel(domazlice_gps[0], domazlice_gps[1])

def get_pixel(latitude, longitude): # -> (x, y)
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

    # coordinates on image
    my_x = avalon_pixel[0] + (dst_ew * dst_ew_dir)
    my_y = avalon_pixel[1] + (dst_ns * dst_ns_dir)

    # check image boundaries
    my_x = int(max(0, min(my_x, composite_size[0])))
    my_y = int(max(0, min(my_y, composite_size[1])))

    # return pixel
    return (int(my_x), int(my_y))

def prepare_data(): # → True if new data was prepared
    now = time.time()
    status = False

    for back in range(10, 40, 10):
        timestamp = get_data_timestamp(back = back)
        status = download(timestamp[1])
        delta = int((now - timestamp[0]) / 60)

        if status:
            log.info('prepare_data(): @+{}m ({}) downloaded.'.format(delta, timestamp[1]))
            break
        else:
            log.error('prepare_data(): @+{}m ({}) failed to download.'.format(delta, timestamp[1]))

    if not status:
        return False

    last_map = last_rain_map()
    map_age = int((timestamp[0] - last_map) / 60)
    if map_age < 10:
        return False

    create_composite()
    return create_map(timestamp[0])

def download(file_timestamp): # → True if succeed
    url_rain = (url_base + url_postfix_rain).format(file_timestamp)
    url_lightning = (url_base + url_postfix_lightning).format(file_timestamp)

    rain = download_image(url_rain, file_rain)
    lightning = download_image(url_lightning, file_lightning)

    if rain and os.path.isfile(file_rain):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_rain, file_rain))

    if lightning and os.path.isfile(file_lightning):
        os.system('convert {} -crop 595x376+2+83 +repage {}'.format(file_lightning, file_lightning))

    return rain and lightning

def download_image(url, path): # → True if succeed
    if os.path.isfile(path):
        os.remove(path)

    try:
        with request.urlopen(url) as response, open(path, 'wb') as file:
            shutil.copyfileobj(response, file)
    except:
        return False

    if os.path.isfile(path):
        return True
    else:
        return False

def create_map(timestamp): # → True if new map was saved.
    if not os.path.isfile(composite):
        return False

    color_map_len = len(color_map)

    map_x = composite_size[0]
    map_y = composite_size[1]
    map = numpy.zeros(shape = (map_x, map_y))

    image = Image.open(composite)
    pixels = image.load()

    # detect rain
    for x in range(composite_size[0]):
        for y in range(composite_size[1]):
            intensity = 0

            px = pixels[x, y]
            r = int(px[0])
            g = int(px[1])
            b = int(px[2])

            for clr in range(color_map_len):
                color = color_map[clr]
                if clr < (color_map_len - 2):
                    color_next = color_map[clr + 1]
                else:
                    color_next = None

                if (color[0] == r and color[1] == g and color[2] == b) or (color_next and (((color[0] <= r < color_next[0]) or (color[0] >= r > color_next[0])) and ((color[1] <= g < color_next[1]) or (color[1] >= g > color_next[1])) and ((color[2] <= b < color_next[2]) or (color[2] >= b > color_next[2])))):
                    intensity = (clr + 1) * 4 # mm/hr

            map[x][y] = intensity

    return store_rain_map(timestamp, map)

def create_composite(): # -> composite filename (string)
    if os.path.isfile(composite):
        os.remove(composite)

    if not os.path.isfile(file_rain) or not os.path.isfile(file_lightning):
        return

    os.system('convert {} {} -geometry +0+0 -composite {}'.format(asset_terrain, asset_cities, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_rain, composite))
    os.system('convert {} {} -geometry +0+0 -composite {}'.format(composite, file_lightning, composite))

    mark_location(get_avalon_pixel(), avalon_radius, composite_avalon)
    mark_location(get_prague_pixel(), prague_radius, composite_prague)
    mark_location(get_pilsen_pixel(), pilsen_radius, composite_pilsen)
    mark_location(get_domazlice_pixel(), domazlice_radius, composite_domazlice)

    return composite

def mark_location(pixel, watch, file):
    x = pixel[0]
    y = pixel[1]
    cx = pixel[0] - watch
    cy = pixel[1] - watch

    os.system('convert {} -fill "rgba(0, 0, 0, 0.0)" -stroke "rgba(0, 0, 0, 0.8)" -strokewidth 2 -draw "circle {},{} {},{}" {}'.format(composite, x, y, cx, cy, file))

def get_data_timestamp(back = 10): # → (timestmap, chmi image timestamp)
    now = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes = back)
    minute = now.minute - math.floor(now.minute / 10) * 10
    now = now - datetime.timedelta(minutes = minute, seconds = now.second)
    
    yr = '{:04d}'.format(now.year)
    mo = '{:02d}'.format(now.month)
    dy = '{:02d}'.format(now.day)
    hr = '{:02d}'.format(now.hour)
    mn = '{:02d}'.format(now.minute)
    timestamp_str = '{}{}{}.{}{}'.format(yr, mo, dy, hr, mn)

    return (math.floor(datetime.datetime.timestamp(now)), timestamp_str)

def store_rain_map(timestamp, map): # → True if new map was saved.
    db = None
    try:
        db = sqlite3.connect(path.to('data/rain_history.sqlite'))
    except:
        log.error('store_rain_map(): unable to open rain database.')
        return False

    cursor = db.cursor()
    try:
        cursor.execute(
            'insert into rain (timestamp, map) values (?, ?)',
            (timestamp, sqlite3.Binary(map.tobytes()))
        )
        db.commit()

        return True
    except sqlite3.Error as error:
        db.close()

        log.error('store_rain_map(): unable to store data: {}'.format(error))
        return False

def load_rain_map(when = None, count = 1): # → (timestamp, map)
    db = _open_database('data/rain_history.sqlite')
    cursor = db.cursor()

    if when:
        cursor.execute('select timestamp, map from rain where timestamp <= {} order by timestamp desc limit 0, {}'.format(when, count))
    else:
        cursor.execute('select timestamp, map from rain order by timestamp desc limit 0, {}'.format(count))

    row = cursor.fetchone()
    db.close()

    if not row:
        return None

    timestamp = row[0]
    map = numpy.frombuffer(row[1], dtype = numpy.float64)
    map = map.reshape(composite_size[0], composite_size[1])

    return (timestamp, map)

def load_rain_maps(since): # → [(timestamp, map)]
    db = _open_database('data/rain_history.sqlite')
    cursor = db.cursor()

    cursor.execute('select timestamp, map from rain where timestamp >= {} order by timestamp desc'.format(since))

    rows = cursor.fetchall()
    db.close()

    if not rows:
        return None

    entries = []
    for row in rows:
        timestamp = row[0]
        map = numpy.frombuffer(row[1], dtype = numpy.float64)
        map = map.reshape(composite_size[0], composite_size[1])

        entries.append((timestamp, map))

    return entries

def last_rain_map(): # → timestamp
    db = _open_database('data/rain_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]

    cursor.execute('select timestamp from rain order by timestamp desc limit 0, 1')

    timestamp = cursor.fetchone()
    db.close()

    return timestamp

def _open_database(file):
    db = None
    try:
        db = sqlite3.connect(path.to(file))
    except:
        log.error('_open_database(): unable to open database "{}".'.format(file))

    return db
