#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.storage as storage

import os
import math
import time
import datetime
import seaborn
import pandas
from pylab import savefig

def post_heatmap():
    dataFrame = pandas.DataFrame(data())
    palette = seaborn.color_palette("ch:s=.25,rot=-.25", as_cmap = True)
    heatmap = seaborn.heatmap(dataFrame, cmap = palette, linewidth = 0.3)

    fig = heatmap.get_figure()
    fig.savefig(path.to('data/heatmap.png'), dpi = 400)

    # todo: post `data/heatmap.png` to twitter

    return

# return 2d array: day-of-the-week × hour-of-the-day
def data():
    idxTimestamp = 0
    idxPresent = 1

    entries = storage.get_presence(asc = True)
    entriesCnt = len(entries)

    data = [
        #0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,20,21,22,23   # hour / day
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # mon
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # tue
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # wed
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # thu
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # fri
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # sat
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # sun
    ]

    entryPrevious = None
    for entry in entries:
        present = entry[idxPresent]
        timestamp = entry[idxTimestamp]
        timestampDelta = 0
        if entryPrevious:
            timestampDelta = timestamp - entryPrevious[idxTimestamp]

        dow = day_of_week(timestamp)
        hod = hour_of_day(timestamp)

        if present == 0 and timestampDelta < 5*60:
            data[dow][hod] += timestampDelta

        entryPrevious = entry

    return data

# returns day of week 0 (mon)..6 (sun)
def day_of_week(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).weekday()

# returns hour of day 0..23
def hour_of_day(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).hour

# returns timestamp of start of the day
def midnight(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp)
    midnight = datetime.datetime.combine(date, datetime.datetime.min.time())

    return = datetime.datetime.timestamp(midnight)
