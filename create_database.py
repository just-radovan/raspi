#!/usr/bin/python3.7

import data.database as database

database.init_netatmo()
database.init_rain()
database.init_presence()
# database.init_location()
