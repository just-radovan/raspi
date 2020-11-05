#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import common.log as log

import os
import math
import time
import datetime
import sqlite3

rain_save = path.to('data/rain_tweet.save')

def lock(label, expiration):
    exp = int(time.time()) + expiration

    file = open(path.to('data/{}.lock'.format(label)), 'w')
    file.write(str(exp))
    file.close()

def is_locked(label):
    check_lock(label)

    return os.path.exists(path.to('data/{}.lock'.format(label)))

def check_lock(label):
    name = 'data/{}.lock'.format(label)

    if not os.path.exists(path.to(name)):
        return

    file = open(path.to(name), 'r')
    expiration = int(file.read())
    file.close()

    if expiration < time.time() and os.path.isfile(path.to(name)):
        os.remove(path.to(name))

def get_presence(asc = False):
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.execute('select timestamp, present from presence order by timestamp {}'.format('asc' if asc else 'desc'))

    rows = cursor.fetchall()
    db.close()

    return rows

def get_location():
    db = _open_database('data/location_history.sqlite')
    cursor = db.cursor()
    cursor.execute('select latitude, longitude, venue from location order by timestamp desc limit 0, 1')

    row = cursor.fetchone()
    db.close()

    latitude = row[0]
    longitude = row[1]
    venue = row[2]

    log.info('get_location(): last known location: {} ({:.5f}, {:.5f})'. format(venue, latitude, longitude))

    return [latitude, longitude, venue]

def is_present():
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select present from presence order by timestamp desc limit 0, 1')

    row = cursor.fetchone()
    db.close()

    isPresent = (row == 1)
    log.info('is_present(): {}'.format("🏡" if isPresent else "🏝"))

    return isPresent

def was_outside():
    entries = 8

    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select present from presence order by timestamp desc limit 0, {}'.format(entries))

    rows = cursor.fetchall()
    db.close()

    return evaluate(rows, 1, 0, 0.3, '🏡', '🏝')

def how_long_outside():
    timeFrom = datetime.datetime.timestamp(datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())) # today's midnight
    timeTo = int(time.time())

    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.execute('select timestamp, present from presence where timestamp between ? and ?', (timeFrom, timeTo))

    rows = cursor.fetchall()
    db.close()

    rowPrevious = None
    outsideStart = -1
    outside = 0
    for row in rows:
        if row[1] == 0:
            if (not rowPrevious or rowPrevious[1] == 1) and outsideStart < 0:
                outsideStart = row[0]
        else:
            if outsideStart >= 0:
                outside += (row[0] - outsideStart)
                outsideStart = -1

        rowPrevious = row

    return outside

def get_netatmo_value(column):
    return get_netatmo_data(column, 1)[0]

def get_netatmo_data(column, count):
    db = _open_database('data/netatmo_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select {} from netatmo order by timestamp desc limit 0, {}'.format(column, count))

    rows = cursor.fetchall()
    db.close()

    return rows

def get_rain_value(column):
    return get_rain_data(column, 1)[0]

def get_rain_data(column, count):
    db = _open_database('data/rain_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select {} from rain order by timestamp desc limit 0, {}'.format(column, count))

    rows = cursor.fetchall()
    db.close()

    return rows

def get_rain():
    return get_rain_when(None)

def get_rain_when(when):
    db = _open_database('data/rain_history.sqlite')
    cursor = db.cursor()

    if when:
        cursor.execute('select timestamp, intensity, distance, area from rain where timestamp <= {} order by timestamp desc limit 0, 1'.format(when))
    else:
        cursor.execute('select timestamp, intensity, distance, area from rain order by timestamp desc limit 0, 1')

    row = cursor.fetchone()
    db.close()

    return row

def save_last_rain_tweeted(timestamp):
    file = open(rain_save, 'w')
    file.write(str(timestamp))
    file.close()

def load_last_rain_tweeted():
    if not os.path.exists(rain_save):
        return

    file = open(rain_save, 'r')
    timestamp = int(file.read())
    file.close()

    return timestamp

# entries: list of numeric values
# threshold: value that decides
# comparison:
# __ -1 = leading values should be below or same as threshold
# __ 0 = leading values should match threshold
# __ +1 = leading values should be above or same as threshold
# required: portion of leading of all entries required to match threshold & comparison (0.0-1.0)
# returns true if conditions are met
def evaluate(entries, threshold, comparison, required, emojiLeading, emojiTrailing):
    leading = True
    found = {'leading': 0, 'trailing': 0}

    entriesCnt = len(entries)
    for entry in entries:
        if _compare(entry, threshold, comparison, not leading):
            if leading:
                found['leading'] += 1
            else:
                found['trailing'] += 1
        else:
            if leading == False:
                break

            leading = False
            found['trailing'] += 1

    requiredCount = int(math.ceil(entriesCnt * required))
    restCount = entriesCnt - requiredCount

    log.info('evaluate(): {} → {} (0..{}) | {} → {} (>={})'.format(emojiLeading, found['leading'], requiredCount, emojiTrailing, found['trailing'], requiredCount, restCount))

    return ((found['leading'] > 0 and found['leading'] <= requiredCount) and found['trailing'] >= restCount)

# entries: list of numeric values (sorted last to first)
# change: change required between each other etry (0.0-1.0)
# return:
# __ +1: it's increasing enough
# __ 0: it's not changing enough
# __ -1: it's decreasing enough
def evaluate_trend(entries, change):
    entries.reverse() # now first entry is oldest, last is most recent

    increasing = 0
    increasingBoundaries = [None, None]
    decreasing = 0
    decreasingBoundaries = [None, None]

    entryPrevious = entries[0]
    for entry in entries[1:]:
        if decreasing >= 0:
            if not decreasingBoundaries[0]:
                decreasingBoundaries[0] = entryPrevious

            if entry <= (entryPrevious - (entryPrevious * change)):
                decreasing += 1
                decreasingBoundaries[1] = entry
            else:
                decreasing = -1
                decreasingBoundaries[1] = entryPrevious

        if increasing >= 0:
            if not increasingBoundaries[0]:
                increasingBoundaries[0] = entryPrevious

            if entry >= (entryPrevious + (entryPrevious * change)):
                increasing += 1
                increasingBoundaries[1] = entry
            else:
                increasing = -1
                increasingBoundaries[1] = entryPrevious

        entryPrevious = entry

    log.info('evaluate_trend(): increased {} ({}→{}) values; decreased {} ({}→{}) values.'.format(increasing, increasingBoundaries[0], increasingBoundaries[1], decreasing, decreasingBoundaries[0], decreasingBoundaries[1]))

    if increasing > decreasing:
        if increasing > 5:
            return [+1] + increasingBoundaries
        else:
            return [0, None, None]
    elif increasing < decreasing:
        if decreasing > 5:
            return [-1] + decreasingBoundaries
        else:
            return [0, None, None]
    else:
        return [0, None, None]

def _compare(value, threshold, comparison, inverted):
    if not inverted:
        return ((comparison == -1 and value <= threshold) or (comparison == 0 and value == threshold) or (comparison == +1 and value >= threshold))
    else:
        return ((comparison == -1 and value > threshold) or (comparison == 0 and value != threshold) or (comparison == +1 and value < threshold))

def _open_database(file):
    db = None
    try:
        db = sqlite3.connect(path.to(file))
    except Error as e:
        log.error('_open_database(): unable to open database "{}": {}'.format(file, e))

    return db
