#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage
import common.chmi as chmi
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
    now = datetime.datetime.now()
    if now.hour < 23:
        log.warning('summary_presence(): outside of operating hours.')
        return

    if storage.is_locked('summary_presence'):
        log.warning('summary_presence(): lock file present.')
        return

    outside = storage.how_long_outside()
    outsideStr = ''
    if outside < 60:
        outsideStr = 'míň než minutu'
    elif outside < 5*60:
        outsideStr = 'miň než pět minut'
    elif outside <= 90*60:
        minutes = int(math.floor(outside / 60))

        outsideStr = '{} minut'.format(minutes)
    else:
        hours = int(math.floor(outside / (60 * 60)))
        minutes = int(math.floor((outside - (hours * 60 * 60)) / 60))

        outsideStr = '{}h{}'.format(hours, minutes)

    twitter.tweet('🚶 dneska si byl venku {}.'.format(outsideStr))
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
      '🛰 vítej na avalonu.',
      '🛰 avalon tě vítá zpět.',
      '🚀 domov, sladký domov.'
    ]
    message = (
        '{}\n\n'
        '✪ co₂: {} ppm\n'
        '✪ teplota: {} °c\n'
        '✪ vlhkost: {} %'
    ).format(random.choice(start), co2, temperature, humidity)

    twitter.tweet(message)
    log.info('summary_at_home(): tweeted.')
    storage.lock('summary_at_home', 30*60)

def summary_morning():
    now = datetime.datetime.now()
    if not (5 < now.hour < 12):
        log.warning('summary_morning(): outside of operating hours.')
        return

    if storage.is_locked('summary_morning'):
        log.warning('summary_morning(): lock file present.')
        return

    if not storage.is_present():
        log.warning('summary_morning(): not at home.')
        return

    entries = 5
    rows = storage.get_netatmo_data('noise', entries)

    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        log.warning('summary_morning(): not noisy enough.')
        return

    temperature = storage.get_netatmo_value('temp_out')
    humidity = storage.get_netatmo_value('humidity_out')
    pressure = storage.get_netatmo_value('pressure')

    start = [
      '🙄 a kurva. další den.',
      '🤪 dobrý ráno!',
      '🏝 další den v ráji...',
      '🤪 čau debile!',
      '🧐 zase den na píču?'
    ]
    message = (
        '{}\n\n'
        '✪ teplota: {} °c\n'
        '✪ tlak vzduchu: {} mb\n'
        '✪ vlhkost: {} %'
    ).format(random.choice(start), temperature, pressure, humidity)

    twitter.tweet(message)
    log.info('summary_morning(): tweeted.')
    storage.lock('summary_morning', 12*60*60)

def noise():
    if storage.is_locked('noise'):
        log.warning('noise(): lock file present.')
        return

    if storage.is_present():
        log.warning('noise(): at home.')
        return

    rows = storage.get_netatmo_data('noise', 4)

    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        log.warning('noise(): no noise detected.')

    twitter.tweet('🔊 je tu hluk i když tu nejsi. aktuálně to je {} db'.format(entries[0]))
    log.info('noise(): tweeted.')
    storage.lock('noise', 15*60)

def co2():
    if storage.is_locked('co2'):
        log.warning('co2(): lock file present.')
        return

    rows = storage.get_netatmo_data('co2', 4)

    if not storage.evaluate(rows, bad_air_threshold, +1, 0.3, '☣️', '💨'):
        log.warning('co2(): co₂ is not above the limit.')
        return

    co2 = int(rows[0])
    twitter.tweet('🤢 chtělo by to vyvětrat. aktuální koncentrace co₂: {} ppm.'.format(co2))
    log.info('co2(): tweeted.')
    storage.lock('co2', 30*60)

def co2_trend():
    if storage.is_locked('co2_trend') or storage.is_locked('co2'):
        log.warning('co2_trend(): lock file present for co2() or co2_trend().')
        return

    rows = storage.get_netatmo_data('co2', 5)
    trend = storage.evaluate_trend(rows, 0.01)

    co2From = 0
    co2To = 0
    if trend[1]:
        co2From = int(trend[1])
    if trend[2]:
        co2To = int(trend[2])

    if trend[0] == +1:
        twitter.tweet('⚠️ koncentrace co₂ rychle roste! {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend+).')
        storage.lock('co2_trend', 60*60)
    elif trend[0] == -1:
        twitter.tweet('👍 paráda, koncentrace co₂ klesá. {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend-).')
        storage.lock('co2_trend', 60*60)

def temperature_outdoor():
    if storage.is_locked('temperature_outdoor'):
        log.warning('temperature_outdoor(): lock file present.')
        return

    if not storage.is_present():
        log.warning('temperature_outdoor(): not at home.')
        return

    rows = storage.get_netatmo_data('temp_out', 4)

    if not storage.evaluate(rows, temp_outdoor_treshold, -1, 0.5, '❄️', '☀️'):
        log.warning('temperature_outdoor(): temperature is not low enough.')
        return

    twitter.tweet('🥶 usměj se než ti ztuhne xicht. venku je jen {} °C.'.format(rows[0]))
    log.info('temperature_outdoor(): tweeted.')
    storage.lock('temperature_outdoor', 30*60)

def radar():
    # timed by cron
    data = chmi.get_rain_intensity()
    radar_tweet(data)

def radar_tweet(data):
    now = datetime.datetime.now()
    if 1 < now.hour < 7:
        log.warning('radar_tweet(): outside of operating hours.')
        return

    if storage.is_locked('radar_tweet'):
        log.warning('radar_tweet(): lock file present.')
        return

    if not data or data[0] <= 4 or data[1] < 3: # at least 4 mm/hr at 3% of the area.
        log.warning('radar_tweet(): not raining enough: {} mm/hr at {} %'.format(data[0], data[1]))
        return

    if not data[1]:
        tweet = '🌧 někde poblíž chčije. prší na {} % sledované oblasti, maximum je {} mm/h.'.format(data[2], data[0])
    elif data[1] < 2:
        tweet = '☔️ chčije! prší na {} % sledované oblasti, maximum je {} mm/h.'.format(data[2], data[0])
    else:
        tweet = '🌧 {:.1f} km od avalonu chčije! prší na {} % sledované oblasti, maximum je {} mm/h.'.format(data[1], data[2], data[0])

    twitter.tweet(tweet, media = [data[3], camera.get_last_photo()])
    log.info('radar_tweet(): tweeted.')
    storage.lock('radar_tweet', 30*60)

def view():
    # timed by cron
    camera.take_photo()

def video():
    # timed by cron
    camera.make_video()
