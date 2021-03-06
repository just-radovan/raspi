# raspi

various scripts to notify me about what's happening at home. via twitter.
also to inform people about rain. also via twitter.

## setup

* install dependencies
* create `auth/*.py` files with oauth tokens for twitter, swarm, and netatmo. see examples.
* run `*_auth.py` to authorize scripts with each respective service. you'll be asked for some manual help.
* run `create_database.py` to init... well, databases.
* run whatever script you want from project root directory.
* setup cron to not run that manually ever again.

## crontab

```
*/5	    *	*	*	*	python3 /usr/local/bin/scripts/check.py # >> /usr/local/bin/scripts/log/log
*/5	    *	*	*	*	python3 /usr/local/bin/scripts/netatmo_download.py # >> /usr/local/bin/scripts/log/log
*/5	    *	*	*	*	python3 /usr/local/bin/scripts/download_checkins.py # >> /usr/local/bin/scripts/log/log

*/10    *	*	*	*	python3 /usr/local/bin/scripts/watch_rain.py # >> /usr/local/bin/scripts/log/log
*/5     *	*	*	*	python3 /usr/local/bin/scripts/watch_rain_mentions.py # >> /usr/local/bin/scripts/log/log
20	    22	*	*	0	python3 /usr/local/bin/scripts/rain_heatmap.py # >> /usr/local/bin/scripts/log/log
```

## dependencies

* python 3.* (preinstalled)
* fswebcam (apt-get) - handling the webcam
* imagemagick (apt-get) - image manipulation
* libatlas-base-dev (apt-get) - ???
* pillow (pip) - python: image processing
* pytz (pip) - python: time zones
* tweepy (pip) - python: twitter client
* foursquare (pip) - python: foursquare/swarm client
* numpy (pip) - python: library to handle numbers
* seaborn (pip) - python: library to visualise numbers
* geopy (pip) - python: precise distance between coordinates
* shapely (pip) - python: polygon analysis
* space mono ([github.com/../spacemono](https://github.com/googlefonts/spacemono)) - font used to annotate timelapse frames
