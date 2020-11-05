#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import auth.swarm as swarm

import foursquare
import json
import sqlite3

access_file = path.to('data/swarm_access.data')

def download_checkins():
    access_token = None

    with open(access_file) as infile:
        data = json.load(infile)
        for access in data['access']:
            access_token = access['token']

    if not access_token:
        log.error('download_checkins(): unable to load access token.')
        return

    client = foursquare.Foursquare(access_token = access_token)
    data = client.users.checkins(params = {'limit': 100})

    db = None
    try:
        db = sqlite3.connect(path.to('data/location_history.sqlite'))
    except:
        log.error('download_checkins(): unable to open location database.')
        return

    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select timestamp from location order by timestamp desc limit 0, 1')
    timestampLast = cursor.fetchone()

    stored = 0
    for checkin in data['checkins']['items']:
        swarm_id = checkin['id']
        timestamp = checkin['createdAt']
        venue = checkin['venue']['name']
        latitude = checkin['venue']['location']['lat']
        longitude = checkin['venue']['location']['lng']

        if timestampLast and timestamp <= timestampLast:
            continue

        sql = (
            'insert into location ('
            'swarm_id, timestamp, latitude, longitude, venue'
            ') values ('
            '?, ?, ?, ?, ?, ?, ?, ?'
            ')'
        )
        cursor.execute(sql, (swarm_id, timestamp, latitude, longitude, venue))
        stored += 1

    db.commit()
    db.close()

    log.info('download_checkins(): stored new {} checkins.'.format(stored))

def authorize():
    client = foursquare.Foursquare(client_id = swarm.get_consumer_key(), client_secret = swarm.get_consumer_secret(), redirect_uri = 'https://www.radovan.be/')
    redirect_url = client.oauth.auth_url()

    print('👉 authorize(): to continue, please visit {}'.format(redirect_url))
    print('⚠️  (please copy the code from url you have been redirected to)')
    verifier = input('verification code? ')

    access_token = client.oauth.get_token(verifier)

    log.info('authorize(): token: {}'.format(access_token))

    # store data

    data = {}
    data['access'] = []
    data['access'].append({
        'token': access_token
        })

    with open(access_file, 'w') as outfile:
        json.dump(data, outfile)
