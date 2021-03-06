# -*- coding: UTF-8 -*-

import path
import common.log as log
import auth.twitter as twitter
import common.storage as storage

import tweepy
import json
from shapely.geometry import Polygon

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

        try:
            log.info('tweet(): tweeting in reply to {} with media ({}×).'.format(in_reply_to, len(ids)))
            api.update_status(status = message, in_reply_to_status_id = in_reply_to, media_ids = ids)
        except tweepy.error.TweepError as error:
            log.error('tweet(): failed to tweet: {}'.format(error))
    else:
        try:
            log.info('tweet(): tweeting in reply to {}.'.format(in_reply_to))
            api.update_status(status = message, in_reply_to_status_id = in_reply_to)
        except tweepy.error.TweepError as error:
            log.error('tweet(): failed to tweet: {}'.format(error))

def mentions(access_data, since_id): # → [(tweet_id, user, text, gps_is_set, latitude, longitude, location_label)]
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

    if since_id and since_id <= 0:
        since_id = None

    for mention in tweepy.Cursor(api.mentions_timeline, since_id = since_id, count = 20).items():
        tweet_id = mention.id # int64
        user = mention.user.screen_name
        text = mention.text
        
        if mention.coordinates:
            gps_is_set = True

            latitude = mention.coordinates.coordinates[1]
            longitude = mention.coordinates.coordinates[0]
            location_label = '{:.3f},{:.3f}'.format(latitude, longitude)
        elif mention.place:
            gps_is_set = True

            location = Polygon(mention.place.bounding_box.coordinates[0])
            latitude = location.centroid.y # not a mistake, geojson has it the otherway around.
            longitude = location.centroid.x
            location_label = mention.place.name
        else:
            gps_is_set = False
            latitude = None
            longitude = None
            location_label = None

        mentions.append((tweet_id, user, text, gps_is_set, latitude, longitude, location_label))

    return mentions

def authorize(access_data):
    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret(), 'oob')
    try:
        redirect_url = auth.get_authorization_url()

        print('👉 authorize(): to continue, please visit {}'.format(redirect_url))
        verifier = input('verification code? ')
    except tweepy.error.TweepError:
        log.error('authorize(): failed to get authorization request token.')
        return

    try:
        auth.get_access_token(verifier)
    except tweepy.error.TweepError:
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
