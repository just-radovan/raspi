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
        return

    if storage.is_locked('summary_presence'):
        return

    outside = storage.how_long_outside()
    outsideStr = ''
    if outside < 60:
        outsideStr = 'necelou minutu'
    elif outside < 5*60:
        outsideStr = 'méně než pět minut'
    elif outside <= 90*60:
        minutes = int(math.floor(outside / 60))

        outsideStr = '{} min.'.format(minutes)
    else:
        hours = int(math.floor(outside / (60 * 60)))
        minutes = int(math.floor((outside - (hours * 60 * 60)) / 60))

        outsideStr = '{}h{}'.format(hours, minutes)

    twitter_avalon.tweet('🚶 Dnes jsi byl venku {}.'.format(outsideStr))
    log.info('summary_presence(): tweeted.')
    storage.lock('summary_presence', 12*60*60)

    return

def summary_at_home():
    if storage.is_locked('summary_at_home'):
        return

    if not storage.was_outside():
        return

    co2 = storage.get_netatmo_value('co2')
    temperature = storage.get_netatmo_value('temp_in')
    humidity = storage.get_netatmo_value('humidity_in')

    start = [
      '🛰 Vítej doma.',
      '🐈‍⬛ Hurá, kočky!',
      '🏝 Aaah, tady nejsou lidi.'
    ]
    message = (
        '{}\n\n'
        '✪ co₂: {} ppm\n'
        '✪ teplota: {} °C\n'
        '✪ vlhkost: {} %'
    ).format(random.choice(start), co2, temperature, humidity)

    twitter_avalon.tweet(message)
    log.info('summary_at_home(): tweeted.')
    storage.lock('summary_at_home', 30*60)

def summary_morning():
    now = datetime.datetime.now()
    if not (5 < now.hour < 12):
        return

    if storage.is_locked('summary_morning'):
        return

    if not storage.is_present():
        return

    rows = storage.get_netatmo_data('noise', 5)
    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        return

    temperature = storage.get_netatmo_value('temp_out')
    humidity = storage.get_netatmo_value('humidity_out')
    pressure = storage.get_netatmo_value('pressure')

    start = [
      '🙄 Geez, další blbej den.',
      '🤪 Ráno, vole!',
      '🏝 Další den v ráji...',
      '🤪 Nečum a něco dělej!',
      '🧐 Další den na hovno?'
    ]

    post = website.on_this_day()
    if post:
        message = (
            '{}\n\n'
            '✪ teplota: {} °C\n'
            '✪ tlak vzduchu: {} mb\n'
            '✪ vlhkost: {} %\n'
            '\n'
            '🔗 {}'
        ).format(random.choice(start), temperature, pressure, humidity, post)
    else:
        message = (
            '{}\n\n'
            '✪ teplota: {} °C\n'
            '✪ tlak vzduchu: {} mb\n'
            '✪ vlhkost: {} %\n'
        ).format(random.choice(start), temperature, pressure, humidity)

    twitter_avalon.tweet(message)
    log.info('summary_morning(): tweeted.')
    storage.lock('summary_morning', 12*60*60)

def noise():
    if storage.is_locked('noise'):
        return

    if storage.is_present():
        return

    rows = storage.get_netatmo_data('noise', 4)

    if not storage.evaluate(rows, sound_treshold, +1, 0.3, '🔊', '🔇'):
        return

    twitter_avalon.tweet('🔊 Doma je nějaký hluk ({} dB)!'.format(rows[0]))
    log.info('noise(): tweeted.')
    storage.lock('noise', 15*60)

def co2():
    if storage.is_locked('co2'):
        return

    rows = storage.get_netatmo_data('co2', 4)

    if not storage.evaluate(rows, bad_air_threshold, +1, 0.3, '☣️', '💨'):
        return

    co2 = int(rows[0])
    twitter_avalon.tweet('🤢 Úroveň CO₂ je {} ppm. Chtělo by to vyvětrat.'.format(co2))
    log.info('co2(): tweeted.')
    storage.lock('co2', 30*60)

def co2_trend():
    if storage.is_locked('co2_trend') or storage.is_locked('co2'):
        return

    rows = storage.get_netatmo_data('co2', 3)
    trend = storage.evaluate_trend(rows, 0.01)

    co2From = 0
    co2To = 0
    if trend[1]:
        co2From = int(trend[1])
    if trend[2]:
        co2To = int(trend[2])

    if trend[0] == +1:
        twitter_avalon.tweet('⚠️ Úroveň CO₂ rychle stoupá! {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend+).')
        storage.lock('co2_trend', 60*60)
    elif trend[0] == -1:
        twitter_avalon.tweet('👍 Paráda! Úroveň CO₂ klesla. {} → {} ppm.'.format(co2From, co2To))
        log.info('co2(): tweeted (trend-).')
        storage.lock('co2_trend', 60*60)

def temperature_outdoor():
    if storage.is_locked('temperature_outdoor'):
        return

    if not storage.is_present():
        return

    rows = storage.get_netatmo_data('temp_out', 4)

    if not storage.evaluate(rows, temp_outdoor_treshold, -1, 0.5, '❄️', '☀️'):
        return

    twitter_avalon.tweet('🥶 Venku mrzne!')
    log.info('temperature_outdoor(): tweeted.')
    storage.lock('temperature_outdoor', 30*60)

def radar():
    # timed by cron
    status = chmi.prepare_data()
    if not status:
        log.warning('radar(): no new data. won\'t try to tweet.')
        return

    tweet_rain(twitter_avalon)
    tweet_rain(twitter_prague)
    tweet_rain(twitter_pilsen)
    tweet_rain(twitter_domazlice)

def tweet_rain(twitter):
    time_last_check = storage.load_rain_tweeted(twitter)
    if not time_last_check:
        storage.save_rain_tweeted(twitter, time.time())
        return

    idx_timestamp = 0
    idx_intensity = 1
    idx_area = 2
    idx_area_outside = 3
    idx_distance = 4

    rain_info_func = getattr(chmi, 'get_{}_rain_info'.format(twitter.id().lower()))
    rain_now = rain_info_func()
    rain_history = rain_info_func(time_last_check)

    if not rain_now or not rain_history:
        return

    time_now = rain_now[idx_timestamp]
    time_last_check = rain_history[idx_timestamp]
    time_delta = int((time_now - time_last_check) / 60) # minutes

    log.info('tweet_rain(): time between data sets: {} mins.'.format(time_delta))
    if time_delta < 10:
        return

    area_delta = rain_now[idx_area] - rain_history[idx_area]
    area_trend = '⇢'
    if area_delta > 0:
        area_trend = '⇡'
    elif area_delta > 0:
        area_trend = '⇣'

    intensity_delta = rain_now[idx_intensity] - rain_history[idx_intensity]
    intensity_trend = '⇢'
    if intensity_delta > 0:
        intensity_trend = '⇡'
    elif intensity_delta < 0:
        intensity_trend = '⇣'

    distance_trend = '⇢'
    if rain_now[idx_distance] >= 0 and rain_history[idx_distance] < 0:
        distance_trend = '⇣'
    elif rain_now[idx_distance] < 0 and rain_history[idx_distance] >= 0:
        distance_trend = '⇡'
    elif rain_now[idx_distance] >= 0 and rain_history[idx_distance] >= 0:
        if rain_now[idx_distance] > rain_history[idx_distance]:
            distance_trend = '⇡'
        elif rain_now[idx_distance] < rain_history[idx_distance]:
            distance_trend = '⇣'

    rain_emoji = '🌦'
    if rain_now[idx_intensity] <= 4:
        rain_emoji = '🌤'
    elif rain_now[idx_intensity] <= 16:
        rain_emoji = '🌦'
    elif rain_now[idx_intensity] <= 40:
        rain_emoji = '🌧'
    elif rain_now[idx_intensity] <= 52:
        rain_emoji = '💦'
    else:
        rain_emoji = '🌊'

    tweet = None

    if rain_now[idx_area] < 0.2 and rain_history[idx_area] < 0.2:
        if rain_now[idx_area_outside] > 2.0 and (rain_now[idx_distance] >= 0 and rain_history[idx_distance] < 0):
            tweet = random.choice([
                '{} Zatím neprší, ale něco se blíží.',
                '{} Neprší. Ale bude!',
                '{} Na obzoru je déšť.',
                '{} Poslední minuty na suchu. Za chvíli asi začne pršet.'
            ]).format(rain_emoji)
    elif rain_now[idx_area] < 0.2 and rain_history[idx_area] >= 0.2:
        if (rain_now[idx_distance] < 0 and rain_history[idx_distance] >= 0) or rain_now[idx_distance] > rain_history[idx_distance]:
            tweet = random.choice([
                '{} Woo-hoo! Už neprší.',
                '{} Paráda! Přestalo pršet.',
                '{} Dost bylo deště!',
                '{} Yay! Můžeme odložit deštníky.'
            ]).format(rain_emoji)
        else:
            tweet = random.choice([
                '{} Už neprší, ale asi brzy zase začne.',
                '{} Užijte si pár minut bez deště.',
                '{} Přestalo pršet, ale zatím bych se neradoval.'
            ]).format(rain_emoji)
    elif rain_now[idx_area] > 3.0:
        if rain_history[idx_area] <= 3.0:
            tweet = random.choice([
                '{} Připravte deštníky, začalo pršet.',
                '{} Někdo si přál déšť? Někdo bude happy.',
                '{} Začalo pršet.',
                '{} Padá. Voda.',
                '{} Tohle není změna klimatu, tohle je změna počasí. Prší.',
                '{} Pošlete šamana domu, už prší.',
                '{} Za ten déšť může Kalousek!'
            ]).format(rain_emoji)
        elif rain_now[idx_intensity] >= (rain_history[idx_intensity] * 2.0):
            if rain_now[idx_area] > 90:
                if rain_now[idx_intensity] <= 16:
                    tweet = '{} Stále prší jen trochu, zato úplně všude.'.format(rain_emoji)
                elif rain_now[idx_intensity] > 52:
                    tweet = '{} Noe, připrav archu!'.format(rain_emoji)
            else:
                tweet = '{} Déšť zesílil.'.format(rain_emoji)
        elif rain_now[idx_intensity] <= (rain_history[idx_intensity] * 0.5):
            tweet = '{} Déšť trochu zeslábl.'.format(rain_emoji)

    if not tweet:
        if (rain_now[idx_distance] < 0 and rain_history[idx_distance] < 0) or (rain_now[idx_distance] < 0 and time_delta > 45):
            log.info('tweet_rain(): not tweeting, but not raining. resetting the clock for {}.'.format(twitter.id()))
            storage.save_rain_tweeted(twitter, time_now)

        return

    # add numbers to the message
    if rain_now[idx_area] > 0.2:
        if twitter.id() == 'avalon':
            tweet += (
                '\n\n'
                '{} prší na {:.1f} % území\n'
                '{} nejvyšší intenzita srážek je {:.0f} mm/h\n'
                '{} prší {:.1f} km od poslední známé lokace'
            ).format(area_trend, rain_now[idx_area], intensity_trend, rain_now[idx_intensity], distance_trend, rain_now[idx_distance])
        else:
            tweet += (
                '\n\n'
                '{} prší na {:.1f} % území\n'
                '{} nejvyšší intenzita srážek je {:.0f} mm/h'
            ).format(area_trend, rain_now[idx_area], intensity_trend, rain_now[idx_intensity])
    elif rain_now[idx_distance] >= 0:
        tweet += (
            '\n\n'
            '{} stále prší {:.1f} km od sledované oblasti'
        ).format(distance_trend, rain_now[idx_distance])

    # check composite for attachment
    composite = path.to('data/chmi/composite_{}.png'.format(twitter.id()))
    if not os.path.isfile(composite):
        return

    log.info('tweet: "{}"'.format(tweet))
    # todo: return to tweeting
    # if twitter.id() == 'avalon':
    #     twitter.tweet(tweet, media = [composite, camera.get_last_photo()])
    # else:
    #     twitter.tweet(tweet, media = composite)

    storage.save_rain_tweeted(twitter, time_now)

def view():
    # timed by cron
    camera.take_photo()

def video():
    # timed by cron
    camera.make_video()
