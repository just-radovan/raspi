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

    temperature = storage.get_netatmo_value('temp_in')
    humidity = storage.get_netatmo_value('humidity_in')
    co2 = storage.get_netatmo_value('co2')

    start = [
      '🛰 welcome at avalon.',
      '🛰 avalon welcomes you back.',
      '🚀 bridge is yours.'
    ]
    message = (
        '{}\n'
        '✪ co2: {} ppm'
        '✪ temperature: {} °c\n'
        '✪ humidity: {} %\n'
    ).format(random.choice(start), co2, temperature, humidity)

    twitter.tweet(message)

def summary_morning():
    if os.path.exists(morning_lock):
        return

    now = datetime.datetime.now()
    if now.hour < 5 or now.hour > 12:
        return

    if not storage.is_present():
        return

    entries = storage.get_netatmo_data('noise', 5)
    if len(entries) < 5:
        return

    cnt = 0
    for entry in entries:
        if cnt < 2 and entry <= (sound_treshold + 1):
            return
        elif cnt >= 2 and entry > (sound_treshold + 1):
            return

        cnt += 1

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
        '{}\n'
        '✪ temperature: {} °c\n'
        '✪ pressure: {} mb'
        '✪ humidity: {} %\n'
    ).format(random.choice(start), temperature, pressure, humidity)

    twitter.tweet(message)

    open(morning_lock, 'a').close()

def noise():
    if storage.is_present():
        return

    entries = storage.get_netatmo_data('noise', 5)
    if len(entries) < 5:
        return

    cnt = 0
    for entry in entries:
        if cnt < 1 and entry < sound_treshold:
            return
        elif cnt >= 1 and value >= sound_treshold:
            return

        cnt += 1

    twitter.tweet('🔊 there is some noise while you\'re away. it\'s currently at {} db'.format(entries[0]))

def co2():
    entries = storage.get_netatmo_data('co2', 10)
    if len(entries) < 10:
        return

    # TODO: check trend & check lower threshold

def temperature_outdoor():
    if not storage.is_present():
        return

    entries = storage.get_netatmo_data('temp_out', 8)
    if len(entries) < 8:
        return

    cnt = 0
    for entry in entries:
        if cnt < 2 and entry > temp_outdoor_treshold:
            return
        elif cnt >= 2 and value <= temp_outdoor_treshold:
            return

        cnt += 1

    twitter.tweet('🥶 your ass will freeze off! outdoor temperature right now: {} °C'.format(entries[0]))

def cat_food():
    if storage.is_present():
        return

    capture = camera.take_photo()
    if capture:
        twitter.tweet('🐈 cat food status', capture)
