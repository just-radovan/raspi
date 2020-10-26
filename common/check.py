#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage
import common.twitter as twitter
import common.camera as camera

import os
import datetime
import math
import random

sound_treshold = 36 # db
temp_outdoor_treshold = 1.0 # oc
bad_air_threshold = 1000 # ppm
fresh_air_threshold = 700 # ppm

def summary_presence():
    if storage.is_locked('summary_presence'):
        log.warning('summary_presence(): lock file present.')
        return

    now = datetime.datetime.now()
    if now.hour < 23:
        log.warning('summary_presence(): outside of operating hours.')
        return

    outside = storage.how_long_outside()
    outsideStr = ''
    if outside < 60:
        outsideStr = 'less than a minute'
    elif outside < 5*60:
        outsideStr = 'less than five minutes'
    elif outside <= 90*60:
        minutes = int(math.floor(outside / 60))

        outsideStr = '{} minutes'.format(minutes)
    else:
        hours = int(math.floor(outside / (60 * 60)))
        minutes = int(math.floor((outside - (hours * 60 * 60)) / 60))

        outsideStr = '{}h{}'.format(hours, minutes)

    twitter.tweet('🚶 you were outside for {} today.'.format(outsideStr))
    log.info('summary_presence(): tweeted.')
    storage.lock('summary_presence', 12*60*60)

    return

def summary_at_home():
    if storage.is_locked('summary_at_home'):
        log.warning('summary_at_home(): lock file present.')
        return

    if not storage.was_outside():
        log.warning('summary_at_home(): was not outside.')
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
        '✪ co₂: {} ppm\n'
        '✪ temperature: {} °c\n'
        '✪ humidity: {} %'
    ).format(random.choice(start), co2, temperature, humidity)

    twitter.tweet(message)
    log.info('summary_at_home(): tweeted.')
    storage.lock('summary_at_home', 30*60)

def summary_morning():
    entries = 5

    if storage.is_locked('summary_morning'):
        log.warning('summary_morning(): lock file present.')
        return

    now = datetime.datetime.now()
    if now.hour < 5 or now.hour > 12:
        log.warning('summary_morning(): outside of operating hours.')
        return

    if not storage.is_present():
        log.warning('summary_morning(): not at home.')
        return

    rows = storage.get_netatmo_data('noise', entries)

    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        log.warning('summary_morning(): not noisy enough.')
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
    log.info('summary_morning(): tweeted.')
    storage.lock('summary_morning', 12*60*60)

def noise():
    entries = 5

    if storage.is_locked('noise'):
        log.warning('noise(): lock file present.')
        return

    if storage.is_present():
        log.warning('noise(): at home.')
        return

    rows = storage.get_netatmo_data('noise', entries)

    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        log.warning('noise(): no noise detected.')

    twitter.tweet('🔊 there is some noise while you\'re away. it\'s currently at {} db'.format(entries[0]))
    log.info('noise(): tweeted.')
    storage.lock('noise', 30*60)

def co2():
    entries = 10

    if storage.is_locked('co2'):
        log.warning('co2(): lock file present.')
        return

    rows = storage.get_netatmo_data('co2', entries)

    if not storage.evaluate(rows, bad_air_threshold, +1, 0.3, '☣️', '💨'):
        log.warning('co2(): co₂ is not above the limit.')
        return

    co2 = int(rows[0])
    twitter.tweet('🤢 there is too much co₂ in the room: {} ppm'.format(co2))
    log.info('co2(): tweeted.')
    storage.lock('co2', 15*60)

def co2_trend():
    entries = 10

    if storage.is_locked('co2_trend') or storage.is_locked('co2'):
        log.warning('co2_trend(): lock file present for co2() or co2_trend().')
        return

    rows = storage.get_netatmo_data('co2', entries)
    trend = storage.evaluate_trend(rows, 0.03) # 3%

    co2From = 0
    co2To = 0
    if trend[1]:
        co2From = int(trend[1])
    if trend[2]:
        co2To = int(trend[2])

    if trend[0] == +1:
        twitter.tweet('⚠️ co₂ concentration rises sharply! {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend+).')
        storage.lock('co2_trend', 15*60)
    elif trend[0] == -1:
        twitter.tweet('👍 co₂ nicely declines. {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend-).')
        storage.lock('co2_trend', 15*60)

def temperature_outdoor():
    entries = 8

    if storage.is_locked('temperature_outdoor'):
        log.warning('temperature_outdoor(): lock file present.')
        return

    if not storage.is_present():
        log.warning('temperature_outdoor(): not at home.')
        return

    rows = storage.get_netatmo_data('temp_out', entries)

    if not storage.evaluate(rows, temp_outdoor_treshold, -1, 0.5, '❄️', '☀️'):
        log.warning('temperature_outdoor(): temperature is not low enough.')
        return

    twitter.tweet('🥶 your ass will freeze off! outdoor temperature right now: {} °C'.format(rows[0]))
    log.info('temperature_outdoor(): tweeted.')
    storage.lock('temperature_outdoor', 30*60)

def view():
    capture = camera.take_photo()

    if storage.is_locked('view'):
        log.warning('view(): lock file present, won\'t tweet.')
        return

    if capture:
        twitter.tweet('📷', capture)
        log.info('view(): tweeted.')
        storage.lock('view', (2*60*60)-5)

def video():
    if storage.is_locked('video'):
        log.warning('video(): lock file present, won\'t tweet.')
        return

    video = camera.make_video()
