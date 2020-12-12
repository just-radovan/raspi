import data.database as database
import common.log as log

try:
    database.init_netatmo()
except:
    log.error('failed to create netatmo database.')

try:
    database.init_rain()
except:
    log.error('failed to create rain database.')

try:
    database.init_presence()
except:
    log.error('failed to create presence database.')

try:
    database.init_location()
except:
    log.error('failed to create location database.')
