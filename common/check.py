#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.storage as storage
import common.twitter as twitter
import common.camera as camera

import os
import datetime
import random

sound_treshold = 35 # db
temp_outdoor_treshold = 1.0 # oc
fresh_air_treshold = 700 # ppm

morning_lock = path.to('data/morning.lock')

def summary_at_home():
    if not storage.was_outside():
        return

    co2 = storage.get_netatmo_value('co2')
    temperature = storage.get_netatmo_value('temp_in')
    humidity = storage.get_netatmo_value('humidity_in')

    start = [
      '🛰 welcome at avalon.',
      '🛰 avalon welcomes you back.',
      '🚀 bridge is yours.'
    ]
    message = (
        '{}\n\n'
        '✪ co2: {} ppm\n'
        '✪ temperature: {} °c\n'
        '✪ humidity: {} %'
    ).format(random.choice(start), co2, temperature, humidity)

    twitter.tweet(message)

def summary_morning():
    entries = 5

    if os.path.exists(morning_lock):
        return

    now = datetime.datetime.now()
    if now.hour < 5 or now.hour > 12:
        return

    if not storage.is_present():
        return

    rows = storage.get_netatmo_data('noise', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        return

    want = 0
    dontWant = 0

    for row in rows:
        if dontWant == 0:
            if row > (sound_treshold + 1):
                want += 1
            else:
                dontWant += 1
        elif row <= (sound_treshold + 1):
            dontWant += 1

    print('noise evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    if want <= 2:
        return

    temperature = storage.get_netatmo_value('temp_out')
    humidity = storage.get_netatmo_value('humidity_out')
    pressure = storage.get_netatmo_value('pressure')

    start = [
      '🙄 fuck! not this day thing again.',
      '🤪 morning bitch!',
      '🏝 another day in paradise...',
      '🤪 oi cunt!',
      '🧐 what a shitshow?'
    ]
    message = (
        '{}\n\n'
        '✪ temperature: {} °c\n'
        '✪ pressure: {} mb\n'
        '✪ humidity: {} %'
    ).format(random.choice(start), temperature, pressure, humidity)

    twitter.tweet(message)

    open(morning_lock, 'a').close()

def noise():
    entries = 5

    if storage.is_present():
        return

    rows = storage.get_netatmo_data('noise', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        return

    want = 0
    dontWant = 0

    for row in rows:
        if dontWant == 0:
            if row > sound_treshold:
                want += 1
            else:
                dontWant += 1
        elif row <= sound_treshold:
            dontWant += 1

    print('noise evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    if want <= 1:
        return

    twitter.tweet('🔊 there is some noise while you\'re away. it\'s currently at {} db'.format(entries[0]))

def co2():
    entries = storage.get_netatmo_data('co2', 10)
    if len(entries) < 10:
        return

    # TODO: check trend & check lower threshold

def temperature_outdoor():
    entries = 8

    if not storage.is_present():
        return

    rows = storage.get_netatmo_data('temp_out', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        return

    want = 0
    dontWant = 0

    for row in rows:
        if dontWant == 0:
            if row <= temp_outdoor_treshold:
                want += 1
            else:
                dontWant += 1
        elif row >= temp_outdoor_treshold:
            dontWant += 1

    print('temperature evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    if want <= 2:
        return

    twitter.tweet('🥶 your ass will freeze off! outdoor temperature right now: {} °C'.format(entries[0]))

def cat_food():
    if storage.is_present():
        return

    capture = camera.take_photo()
    if capture:
        twitter.tweet('🐈 cat food status', capture)
