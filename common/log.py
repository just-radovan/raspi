# -*- coding: UTF-8 -*-

import datetime

def info(message):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    print('ℹ️   {} • {}'.format(timestamp, message))

def warning(message):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    print('⚠️   {} • {}'.format(timestamp, message))

def error(message):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    print('🛑  {} • {}'.format(timestamp, message))
