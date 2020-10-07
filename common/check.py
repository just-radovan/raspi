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
        print('❌ summary_at_home(): was not outside.')
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
    print('✅ summary_at_home(): tweeted.')

def summary_morning():
    entries = 5

    if os.path.exists(morning_lock):
        print('❌ summary_morning(): lock file present.')
        return

    now = datetime.datetime.now()
    if now.hour < 5 or now.hour > 12:
        print('❌ summary_morning(): outside of operating hours.')
        return

    if not storage.is_present():
        print('❌ summary_morning(): not at home.')
        return

    rows = storage.get_netatmo_data('noise', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        print('❌ summary_morning(): not enough entries in database.')
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

    print('🤔 summary_morning(): noise evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    if want <= 2:
        print('❌ summary_morning(): not noisy long enough.')
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
    print('✅ summary_morning(): tweeted.')

    open(morning_lock, 'a').close()

def noise():
    entries = 5

    if storage.is_present():
        print('❌ noise(): at home.')
        return

    rows = storage.get_netatmo_data('noise', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        print('❌ noise(): not enough entries in database.')
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

    print('🤔 noise(): noise evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    if want <= 1:
        print('❌ noise(): no noise detected.')
        return

    twitter.tweet('🔊 there is some noise while you\'re away. it\'s currently at {} db'.format(entries[0]))
    print('✅ noise(): tweeted.')

def co2():
    entries = 10

    rows = storage.get_netatmo_data('co2', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        print('❌ co2(): not enough entries in database.')
        return

    # TODO: check trend & check lower threshold

    print('✅ co2(): tweeted.')

def temperature_outdoor():
    entries = 8

    if not storage.is_present():
        print('❌ temperature_outdoor(): not at home.')
        return

    rows = storage.get_netatmo_data('temp_out', entries)
    rowsCnt = len(rows)

    if rowsCnt < entries:
        print('❌ temperature_outdoor(): not enough entries in database.')
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
        print('❌ temperature_outdoor(): temperature is not low enough.')
        return

    twitter.tweet('🥶 your ass will freeze off! outdoor temperature right now: {} °C'.format(entries[0]))
    print('✅ temperature_outdoor(): tweeted.')

def cat_food():
    if storage.is_present():
        print('❌ cat_food(): at home.')
        return

    capture = camera.take_photo()
    if capture:
        twitter.tweet('🐈 cat food status', capture)
        print('✅ cat_food(): tweeted.')
