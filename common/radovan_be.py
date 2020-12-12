#!python3.8
# -*- coding: UTF-8 -*-

import path
import common.log as log
import common.storage as storage

import os
import random
import datetime
import requests

url_template = 'https://radovan.be/day/{d:02d}{m:02d}{y:04d}'

def on_this_day(): # -> post url (string)
    now = datetime.datetime.now()

    posts = []
    for year in range(2018, now.year + 1):
        url_post = url_template.format(d = now.day, m = now.month, y = year)

        request = requests.get(url_post)
        if request.status_code == 200:
            posts.append(url_post)

    if len(posts) == 0:
        return

    return random.choice(posts)
