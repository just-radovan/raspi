# -*- coding: UTF-8 -*-

import path
import common.log as log
import auth.twitter as twitter
import common.storage as storage

import tweepy
import json

def id():
    return None

def tweet(access_data, message, in_reply_to = None, media = None):
    access_token = None
    access_secret = None

    with open(access_data) as infile:
        data = json.load(infile)
        for access in data['access']:
            access_token = access['token']
            access_secret = access['token_secret']

    if not access_token or not access_secret:
        log.error('tweet(): unable to load access tokens.')
        return

    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret())
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth)

    if media:
        ids = []
        if isinstance(media, list):
            for media_item in media:
                img = api.media_upload(media_item)
                ids.append(img.media_id_string)
        else:
            img = api.media_upload(media)
            ids.append(img.media_id_string)

        api.update_status(status = message, in_reply_to_status_id = in_reply_to, media_ids = ids)
    else:
        api.update_status(status = message, in_reply_to_status_id = in_reply_to)

def mentions(access_data, since_id): # → [(tweet_id, user, text, gps_is_set, latitude, longitude)]
    mentions = []
    access_token = None
    access_secret = None

    with open(access_data) as infile:
        data = json.load(infile)
        for access in data['access']:
            access_token = access['token']
            access_secret = access['token_secret']

    if not access_token or not access_secret:
        log.error('mentions(): unable to load access tokens.')
        return mentions

    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret())
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth)

    for mention in tweepy.Cursor(api.mentions_timeline, since_id = since_id, count = 20).items():
        tweet_id = mention.id # int64
        user = mention.user.screen_name
        text = mention.text
        
        if mention.coordinates:
            # geojson is long, then lat.
            gps_is_set = True
            latitude = mention.coordinates[1]
            longitude = mention.coordinates[0]
        else:
            gps_is_set = False
            latitude = None
            longitude = None

        mentions.append((tweet_id, user, text, gps_is_set, latitude, longitude))

    return mentions

def authorize(access_data):
    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret(), 'oob')
    try:
        redirect_url = auth.get_authorization_url()

        print('👉 authorize(): to continue, please visit {}'.format(redirect_url))
        verifier = input('verification code? ')
    except tweepy.TweepError:
        log.error('authorize(): failed to get authorization request token.')
        return

    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        log.error('authorize(): failed to get access token.')
        return

    access_token = auth.access_token
    access_secret = auth.access_token_secret

    # store data
    data = {}
    data['access'] = []
    data['access'].append({
        'token': access_token,
        'token_secret': access_secret
    })

    with open(access_data, 'w') as outfile:
        json.dump(data, outfile)
