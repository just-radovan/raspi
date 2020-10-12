#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path

import os
import math
import time
import datetime
import sqlite3

def lock(label, expiration):
    exp = int(time.time()) + expiration

    file = open(path.to('data/{}.lock'.format(label)), 'w')
    file.write(str(exp))
    file.close()

    return

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

    if expiration < time.time():
        os.remove(path.to(name))

def get_presence(asc = False):
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select timestamp, present from presence order by timestamp {} limit'.format('asc' if asc else 'desc'))

    rows = cursor.fetchall()
    db.close()

    return rows

def is_present():
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select present from presence order by timestamp desc limit 0, 1')

    row = cursor.fetchone()
    db.close()

    isPresent = (row == 1)
    print('✅ is_present(): {}'.format("🏡" if isPresent else "🏝"))

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

    print('🤔 evaluate(): {} → {} (0..{}) | {} → {} (>={})'.format(emojiLeading, found['leading'], requiredCount, emojiTrailing, found['trailing'], requiredCount, restCount))

    return ((found['leading'] > 0 and found['leading'] <= requiredCount) and found['trailing'] >= restCount)

# entries: list of numeric values (sorted last to first)
# change: change required between each other etry (0.0-1.0)
# return:
# __ +1: it's increasing enough
# __ 0: it's not changing enough
# __ -1: it's decreasing enough
def evaluate_trend(entries, change):
    increasing = 0
    increasingBoundaries = [None, None]
    decreasing = 0
    decreasingBoundaries = [None, None]

    entryPrevious = None
    for entry in entries:
        if entryPrevious:
            if decreasing >= 0:
                if entry > (entryPrevious + (entryPrevious * change)):
                    decreasing += 1
                    if not decreasingBoundaries[1]:
                        decreasingBoundaries[1] = entryPrevious
                else:
                    decreasing = -1
                    if not decreasingBoundaries[0]:
                        decreasingBoundaries[0] = entryPrevious

            if increasing >= 0:
                if entry < (entryPrevious - (entryPrevious * change)):
                    increasing += 1
                    if not increasingBoundaries[1]:
                        increasingBoundaries[1] = entryPrevious
                else:
                    increasing = -1
                    if not increasingBoundaries[0]:
                        increasingBoundaries[0] = entryPrevious

        entryPrevious = entry

    print('🤔 evaluate_trend(): increased {} ({}→{}) values; decreased {} ({}→{}) values.'.format(increasing, increasingBoundaries[0], increasingBoundaries[1], decreasing, decreasingBoundaries[0], decreasingBoundaries[1]))

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
        print('❌ _open_database(): unable to open database "{}": {}'.format(file, e))

    return db
