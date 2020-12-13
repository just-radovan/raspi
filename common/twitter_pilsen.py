# -*- coding: UTF-8 -*-

import path
import common.twitter as twitter

import tweepy
import json

def id():
    return 'pilsen'

def tweet(message, media = None):
    access_data = path.to('data/twitter_access.data')
    twitter.tweet(access_data, message, media)

def authorize():
    access_data = path.to('data/twitter_access.data')
    twitter.authorize(access_data)