#!/usr/bin/python3.7

import path

import sqlite3

def is_present():
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.execute('select "present" from presence order by "timestamp" desc limit 0, 1')

    row = cursor.fetchone()[0]
    db.close()

    return (row == 1)

def was_outside():
    db = _open_database('data/presence_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select "present" from presence order by "timestamp" desc limit 0, 5')

    rows = cursor.fetchall()
    db.close()

    cnt = 0
    for row in rows:
        if cnt == 0 and row == 0:
            return False
        elif cnt >= 0 and row == 1:
            return False

        cnt += 1

    return True

def get_netatmo_value(column):
    return get_netatmo_data(column, 1)[0]

def get_netatmo_data(column, count):
    db = _open_database('data/netatmo_history.sqlite')
    cursor = db.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute('select "{}" from netatmo order by "timestamp" desc limit 0, {}'.format(column, count))

    rows = cursor.fetchall()
    db.close()

    return rows

def _open_database(file):
    db = None
    try:
        db = sqlite3.connect(path.to(file))
    except Error as e:
        print('unable to open database "{}": {}'.format(file, e))

    return db
