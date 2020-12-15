# -*- coding: UTF-8 -*-

import path
import common.twitter as twitter

import tweepy
import json

auth_file = 'data/twitter_access_domazlice.data'

def id():
    return 'domazlice'

def tweet(message, media = None):
    access_data = path.to(auth_file)
    twitter.tweet(access_data, message, media)

def authorize():
    access_data = path.to(auth_file)
    twitter.authorize(access_data)