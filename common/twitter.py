#!/usr/bin/python3.7

import path
import auth.twitter as twitter

import tweepy
import json

def tweet(message, media = None):
    accessToken = ''
    accessTokenSecret = ''

    with open(path.to('data/twitter_access.data')) as infile:
        data = json.load(infile)
        for access in data['access']:
            accessToken = access['token']
            accessTokenSecret = access['token_secret']

    if not accessToken or not accessTokenSecret:
        print('unable to load access tokens.')
        quit()

    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret())
    auth.set_access_token(accessToken, accessTokenSecret)

    api = tweepy.API(auth)

    if media:
        img = api.media_upload(media)
        api.update_status(status = message, media_ids = [img.media_id_string])
    else:
        api.update_status(status = message)

def authorize():
    auth = tweepy.OAuthHandler(twitter.get_consumer_key(), twitter.get_consumer_secret(), 'oob')
    try:
        redirect_url = auth.get_authorization_url()
        print('to continue, please visit ' + redirect_url)

        verifier = input('verification code? ')
    except tweepy.TweepError:
        print('failed to get authorization request token.')
        quit()

    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        print('failed to get access token.')
        quit()

    accessToken = auth.access_token
    accessSecret = auth.access_token_secret

    print('tokens: ' + accessToken + ', ' + accessSecret)

    # store data

    data = {}
    data['access'] = []
    data['access'].append({
        'token': accessToken,
        'token_secret': accessSecret
        })

    with open(path.to('data/twitter_access.data'), 'w') as outfile:
        json.dump(data, outfile)
