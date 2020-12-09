#!/usr/bin/python3.7

import path

import sqlite3

def init_netatmo():
    sql = (
        'create table netatmo ('
        '"id" integer primary key autoincrement, '
        '"timestamp" integer, "temp_in" real, "temp_out" real, '
        '"humidity_in" real, "humidity_out" real, "pressure" real, '
        '"noise" real, "co2" real'
        ')'
    )

    db = None
    try:
        db = sqlite3.connect(path.to('data/netatmo_history.sqlite'))
    except Error as e:
        print('unable to open netatmo database: {}'.format(e))
        quit()

    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()

def init_rain():
    sql = (
        'create table rain ('
        '"id" integer primary key autoincrement, '
        '"timestamp" integer, "intensity" real, "distance" real, "area" real, '
        '"intensity_prg" real, "area_prg" real, '
        '"intensity_pils" real, "area_pils" real, '
        '"intensity_dom" real, "area_dom" real'
        ')'
    )

    db = None
    try:
        db = sqlite3.connect(path.to('data/rain_history.sqlite'))
    except Error as e:
        print('unable to open rain database: {}'.format(e))
        quit()

    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()

def init_presence():
    sql = (
        'create table presence ('
        '"id" integer primary key autoincrement, '
        '"timestamp" integer, "present" integer'
        ')'
    )

    db = None
    try:
        db = sqlite3.connect(path.to('data/presence_history.sqlite'))
    except Error as e:
        print('unable to open presence database: {}'.format(e))
        quit()

    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()

def init_location():
    sql = (
        'create table location ('
        '"id" integer primary key autoincrement, '
        '"swarm_id" text not null unique, '
        '"timestamp" integer, "latitude" real, "longitude" real, "venue" text'
        ')'
    )

    db = None
    try:
        db = sqlite3.connect(path.to('data/location_history.sqlite'))
    except Error as e:
        print('unable to open location database: {}'.format(e))
        quit()

    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
