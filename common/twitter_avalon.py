# -*- coding: UTF-8 -*-

import path
import common.twitter as twitter

import tweepy
import json

auth_file = 'data/twitter_access_avalon.data'

def id():
    return 'avalon'

def tweet(message, in_reply_to = None, media = None):
    access_data = path.to(auth_file)
    twitter.tweet(access_data, message, in_reply_to, media)

def mentions(since_id):
    access_data = path.to(auth_file)
    return twitter.mentions(access_data, since_id)

def authorize():
    access_data = path.to(auth_file)
    twitter.authorize(access_data)