# -*- coding: UTF-8 -*-

import datetime

def info(message, no_start = False, allow_continue = False):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    log = ''
    if no_start:
        log = message
    else:
        log = 'ℹ️   {} • {}'.format(timestamp, message)

    if allow_continue:
        print(log, end = '', flush = True)
    else:
        print(log)

def warning(message, no_start = False, allow_continue = False):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    log = ''
    if no_start:
        log = message
    else:
        log = '⚠️   {} • {}'.format(timestamp, message)
    
    if allow_continue:
        print(log, end = '', flush = True)
    else:
        print(log)

def error(message, no_start = False, allow_continue = False):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    log = ''
    if no_start:
        log = message
    else:
        log = '🛑  {} • {}'.format(timestamp, message)
    
    if allow_continue:
        print(log, end = '', flush = True)
    else:
        print(log)
