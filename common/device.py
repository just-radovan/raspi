#!/usr/bin/python3.7
# -*- coding: UTF-8 -*-

import path
import configuration.config as config

import os
import time
import sqlite3

def ping():
    db = None
    try:
        db = sqlite3.connect(path.to('data/presence_history.sqlite'))
    except Error as e:
        print('unable to open presence database: {}'.format(e))
        return

    cursor = db.cursor()
    cursor.execute(
        'insert into presence ("timestamp", "present") values (?, ?)',
        (int(time.time()), 1 if is_device_present() else 0)
    )

    db.commit()
    db.close()

def is_device_present():
    result = os.system('l2ping -c 1 "{}" 2>&1 > /dev/null'.format(config.get_iphone_mac()))
    return (result == 0)
