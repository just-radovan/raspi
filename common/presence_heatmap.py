#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.storage as storage
import common.twitter as twitter

import os
import math
import time
import datetime
import seaborn
import pandas
from pylab import savefig

def post_heatmap():
    if storage.is_locked('post_heatmap'):
        print('❌ post_heatmap(): lock file present.')
        return

    dataFrame = pandas.DataFrame(data())

    palette = seaborn.color_palette('YlOrBr', as_cmap = True)
    heatmap = seaborn.heatmap(dataFrame, cmap = palette, cbar = False)
    heatmapFile = path.to('data/heatmap.png')

    os.remove(heatmapFile)

    fig = heatmap.get_figure()
    fig.savefig(heatmapFile, dpi = 400)

    twitter.tweet('🏝', heatmapFile)
    print('✅ post_heatmap(): tweeted.')
    storage.lock('post_heatmap', 24*60*60)

# return 2d array: day-of-the-week × hour-of-the-day
def data():
    idxTimestamp = 0
    idxPresent = 1

    entries = storage.get_presence(asc = True)
    entriesCnt = len(entries)

    data = {
        'mon': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'tue': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'wed': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'thu': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'fri': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'sat': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'sun': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }

    entryPrevious = None
    for entry in entries:
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        present = entry[idxPresent]
        timestamp = entry[idxTimestamp]

        timestampDelta = 0
        if entryPrevious:
            timestampDelta = timestamp - entryPrevious[idxTimestamp]

        dow = day_of_week(timestamp)
        hod = hour_of_day(timestamp)

        if present == 0 and timestampDelta < 5*60:
            data[days[dow]][hod] += timestampDelta

        entryPrevious = entry

    return data

# returns day of week 0 (mon)..6 (sun)
def day_of_week(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).weekday()

# returns hour of day 0..23
def hour_of_day(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).hour
