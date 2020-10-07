#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path

import sqlite3

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
    rowsCnt = len(rows)
    db.close()

    want = 0
    dontWant = 0

    for row in rows:
        if dontWant == 0:
            if row == 1:
                want += 1
            else:
                dontWant += 1
        elif row == 1:
            dontWant += 1

    print('🤔 was_outside(): presence evaluation: 👍 {} | 👎 {} of {}'.format(want, dontWant, rowsCnt))

    return (rowsCnt == entries and want <= 3)

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

def _open_database(file):
    db = None
    try:
        db = sqlite3.connect(path.to(file))
    except Error as e:
        print('❌ _open_database(): unable to open database "{}": {}'.format(file, e))

    return db
