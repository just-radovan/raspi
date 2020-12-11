#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage
import common.camera as camera
import common.radovan_be as website
import common.chmi as chmi
import common.twitter_avalon as twitter_avalon
import common.twitter_prague as twitter_prague
import common.twitter_pilsen as twitter_pilsen
import common.twitter_domazlice as twitter_domazlice

import os
import time
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
        outsideStr = 'less than a minute'
    elif outside < 5*60:
        outsideStr = 'less than five minutes'
    elif outside <= 90*60:
        minutes = int(math.floor(outside / 60))

        outsideStr = '{} mins'.format(minutes)
    else:
        hours = int(math.floor(outside / (60 * 60)))
        minutes = int(math.floor((outside - (hours * 60 * 60)) / 60))

        outsideStr = '{}h{}'.format(hours, minutes)

    twitter.tweet('🚶 today you were outside for {}.'.format(outsideStr))
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
      '🛰 avalon welcomes you.',
      '🛰 welcome back on avalon.',
      '🚀 home, sweet home.'
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

    rows = storage.get_netatmo_data('noise', 5)
    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        log.warning('summary_morning(): not noisy enough.')
        return

    temperature = storage.get_netatmo_value('temp_out')
    humidity = storage.get_netatmo_value('humidity_out')
    pressure = storage.get_netatmo_value('pressure')
    rain_dst = storage.get_rain_value('distance')

    start = [
      '🙄 fuck. another day.',
      '🤪 morning bitch!',
      '🏝 another day in paradise...',
      '🤪 oi cunt!',
      '🧐 another shitty day?'
    ]

    if rain_dst < 0:
        rain_text = 'none'
    elif 0 <= rain_dst < 2:
        rain_text = 'yup'
    else:
        rain_text = 'rains {:.1f} km away'.format(rain_dst)

    post = website.on_this_day()
    if post:
        message = (
            '{}\n\n'
            '✪ temperature: {} °c\n'
            '✪ rain: {}\n'
            '✪ pressure: {} mb\n'
            '✪ humidity: {} %\n'
            '\n'
            '🔗 {}'
        ).format(random.choice(start), temperature, rain_text, pressure, humidity, post)
    else:
        message = (
            '{}\n\n'
            '✪ temperature: {} °c\n'
            '✪ rain: {}\n'
            '✪ pressure: {} mb\n'
            '✪ humidity: {} %'
        ).format(random.choice(start), temperature, rain_text, pressure, humidity)

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

    twitter.tweet('🔊 you aren\'t at home, yet there is some noise: {} db'.format(entries[0]))
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
    twitter.tweet('🤢 current co₂ level is {} ppm. don\'t you want to open a window?'.format(co2))
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
        twitter.tweet('⚠️ co₂ concentration is rising quickly! {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend+).')
        storage.lock('co2_trend', 60*60)
    elif trend[0] == -1:
        twitter.tweet('👍 nice! co₂ level drops. {} → {} ppm.'.format(co2From, co2To))
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

    twitter.tweet('🥶 your ass will face off. it\'s just {} °c outside.'.format(rows[0]))
    log.info('temperature_outdoor(): tweeted.')
    storage.lock('temperature_outdoor', 30*60)

def radar():
    # timed by cron
    chmi.prepare_data()

    tweet_rain(twitter_avalon)
    tweet_rain(twitter_prague)
    tweet_rain(twitter_pilsen)
    tweet_rain(twitter_domazlice)

def tweet_rain(twitter):
    timestamp = storage.load_rain_tweeted(twitter)
    if not timestamp:
        storage.save_rain_tweeted(twitter, rain_now[0])
        return

    rain_info_func = getattr(chmi, 'get_{}_rain_info'.format(twitter.id().lower()))

    rain_now = rain_info_func()
    rain_history = rain_info_func(timestamp)

    idx_intensity = 0
    idx_distance = 1
    idx_area = 2

    if not rain_now or not rain_history:
        return

    tweet = None

    if rain_now[idx_area] == 0 and rain_history[idx_area] > 0:
        tweet = (
            '🌤 Yay. Už neprší.'
        )
    elif rain_now[idx_area] > 5:
        if rain_history[idx_area] <= 5:
            tweet = (
                '☔️ Někde v poblíž začalo pršet.\n\n'
                '✪ prší na {:.0f} % území\n'
                '✪ nejvyšší intenzita srážek je {:.0f} mm/h'
            ).format(rain_now[idx_area], rain_now[idx_instensity])
        elif rain_now[idx_instensity] >= (rain_history[idx_instensity] * 2.0):
            tweet = (
                '💦 Prší víc a víc.\n\n'
                '✪ prší na {:.0f} % území\n'
                '✪ max. intenzita srážek se změnila z {:.0f} na {:.0f} mm/h'
            ).format(rain_now[idx_area], rain_history[idx_instensity], rain_now[idx_instensity])
        elif rain_now[idx_instensity] <= (rain_history[idx_instensity] * 0.5):
            tweet = (
                '🌦 Zdá se, že přestává pršet.\n\n'
                '✪ prší na {:.0f} % území\n'
                '✪ max. intenzita srážek se změnila z {:.0f} na {:.0f} mm/h'
            ).format(rain_now[idx_area], rain_history[idx_instensity], rain_now[idx_instensity])

    if not tweet:
        return

    composite = path.to('data/chmi/composite_{}.png'.format(twitter.id()))
    if not os.path.isfile(composite):
        log.error('tweet_rain(): composite image is missing.')
        return

    twitter.tweet(tweet, media = composite)
    storage.save_rain_tweeted(twitter, rain_now[column_timestamp])
    log.info('tweet_rain(): tweeted for {}.'.format(twitter.id()))

def view():
    # timed by cron
    camera.take_photo()

def video():
    # timed by cron
    camera.make_video()
