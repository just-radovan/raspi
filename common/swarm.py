#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log
import auth.swarm as swarm

import foursquare
import json

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
    checkins = client.users.checkins(params = {'limit': 100})

    print(checkins)

    # todo: store to database

def authorize():
    client = foursquare.Foursquare(client_id = swarm.get_consumer_key(), client_secret = swarm.get_consumer_secret(), redirect_uri = 'https://www.radovan.be/')
    redirect_url = client.oauth.auth_url()

    print('👉 authorize(): to continue, please visit {}'.format(redirect_url))
    print('⚠️ (please copy access token from url you have been redirected to)')
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
