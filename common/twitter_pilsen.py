# -*- coding: UTF-8 -*-

import path
import common.twitter as twitter

import tweepy
import json

auth_file = 'data/twitter_access_pilsen.data'

def id():
    return 'pilsen'

def tweet(message, in_reply_to = None, media = None):
    access_data = path.to(auth_file)
    twitter.tweet(access_data, message, media)

def mentions(since_id):
    access_data = path.to(auth_file)
    return twitter.mentions(access_data, since_id)
    
def authorize():
    access_data = path.to(auth_file)
    twitter.authorize(access_data)