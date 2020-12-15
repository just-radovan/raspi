# -*- coding: UTF-8 -*-

import path
import common.log as log
import auth.netatmo as netatmo

import time
import json
import sqlite3
from urllib import request, parse

def authorize():
    accessToken = ''
    refreshToken = ''
    expiresIn = 0

    # download data

    data = parse.urlencode({
        'grant_type': 'password',
        'scope': 'read_station',
        'username': netatmo.get_username(),
        'password': netatmo.get_password(),
        'client_id': netatmo.get_consumer_key(),
        'client_secret': netatmo.get_consumer_secret(),
    }).encode()
    req = request.Request('https://api.netatmo.net/oauth2/token', data = data)

    with request.urlopen(req) as response:
        data = json.loads(response.read().decode())

        accessToken = data['access_token']
        refreshToken = data['refresh_token']
        expiresIn = data['expires_in']

    if not accessToken or not refreshToken:
        log.error('failed to obtain tokens.')
        return

    log.info('authorize(): tokens → ' + accessToken + ', ' + refreshToken)

    # store data

    data = {}
    data['access'] = []
    data['access'].append({
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'expiration': int(time.time()) + expiresIn
        })

    with open(path.to('data/netatmo_access.data'), 'w') as outfile:
        json.dump(data, outfile)

def auth_refresh():
    refreshToken = ''
    expiration = 0

    with open(path.to('data/netatmo_access.data')) as infile:
        data = json.load(infile)
        for access in data['access']:
            refreshToken = access['refresh_token']
            expiration = access['expiration']

    if expiration > (time.time() + 3600): # expiration in more than one hour
        log.error('auth_refresh(): no need to refresh authorization.')
        return

    if not refreshToken:
        log.error('auth_refresh(): unable to load refresh tokens.')
        return

    # download data

    accessToken = ''
    expiresIn = 0

    data = parse.urlencode({
        'grant_type': 'refresh_token',
        'client_id': netatmo.get_consumer_key(),
        'client_secret': netatmo.get_consumer_secret(),
        'refresh_token': refreshToken
    }).encode()
    req = request.Request('https://api.netatmo.net/oauth2/token', data = data)

    with request.urlopen(req) as response:
        data = json.loads(response.read().decode())

        accessToken = data['access_token']
        refreshToken = data['refresh_token']
        expiresIn = data['expires_in']

    if not accessToken or not refreshToken:
        log.error('auth_refresh(): failed to obtain tokens.')
        return

    log.info('auth_refresh(): tokens → ' + accessToken + ', ' + refreshToken)

    # store data

    data = {}
    data['access'] = []
    data['access'].append({
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'expiration': int(time.time()) + expiresIn
        })

    with open(path.to('data/netatmo_access.data'), 'w') as outfile:
        json.dump(data, outfile)

def download():
    auth_refresh()

    accessToken = ''

    with open(path.to('data/netatmo_access.data')) as infile:
        data = json.load(infile)
        for access in data['access']:
            accessToken = access['access_token']

    if not accessToken:
        log.error('download(): unable to load access tokens.')
        return

    # download data

    timestamp = 0
    pressure = 0.0
    co2 = 0
    humiIndoor = 0
    humiOutdoor = 0
    noise = 0
    tempIndoor = 0.0
    tempOutdoor = 0.0

    data = parse.urlencode({
        'access_token': accessToken
    }).encode()
    req = request.Request('https://api.netatmo.com/api/getstationsdata', data = data)

    with request.urlopen(req) as response:
        data = json.loads(response.read().decode())

        indoor = data['body']['devices'][0]['dashboard_data']
        outdoor = data['body']['devices'][0]['modules'][0]['dashboard_data']

        timestamp = indoor['time_utc']
        pressure = indoor['Pressure']
        co2 = indoor['CO2']
        humiIndoor = indoor['Humidity']
        humiOutdoor = outdoor['Humidity']
        noise = indoor['Noise']
        tempIndoor = indoor['Temperature']
        tempOutdoor = outdoor['Temperature']

    # store data

    db = None
    try:
        db = sqlite3.connect(path.to('data/netatmo_history.sqlite'))
    except Error as e:
        log.error('download(): unable to open netatmo database: {}'.format(e))
        return

    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select timestamp from netatmo order by timestamp desc limit 0, 1')
    timestampLast = cursor.fetchone()

    if timestamp == timestampLast:
        log.error('download(): timestamp {} already saved'.format(timestamp))
        db.close()
        return

    sql = (
        'insert into netatmo ('
        'timestamp, temp_in, temp_out, humidity_in, humidity_out, pressure, noise, co2'
        ') values ('
        '?, ?, ?, ?, ?, ?, ?, ?'
        ')'
    )
    cursor.execute(sql, (timestamp, tempIndoor, tempOutdoor, humiIndoor, humiOutdoor, pressure, noise, co2))

    db.commit()
    db.close()
