# raspi

various scripts to notify me about what's happening at home. via twitter.

## crontab

```
*	*	*	*	*	/usr/local/bin/scripts/ping_device.py # >> /usr/local/bin/scripts/log/log
*/5	*	*	*	*	/usr/local/bin/scripts/check.py # >> /usr/local/bin/scripts/log/log
*/5	*	*	*	*	/usr/local/bin/scripts/netatmo_download.py # >> /usr/local/bin/scripts/log/log
*/10	*	*	*	*	/usr/local/bin/scripts/watch_rain.py # >> /usr/local/bin/scripts/log/log
*/2	*	*	*	*	/usr/local/bin/scripts/take_photo.py # >> /usr/local/bin/scripts/log/log
55	23	*	*	*	/usr/local/bin/scripts/make_video.py # >> /usr/local/bin/scripts/log/log
10	22	*	*	0	/usr/local/bin/scripts/presence_heatmap.py # >> /usr/local/bin/scripts/log/log

15	0	*	*	*	cp /usr/local/bin/scripts/data/* /mnt/storage/backup/
20	0	*	*	*	cp /usr/local/bin/scripts/data/video/* /mnt/storage/movies/timelapse/ && rm /usr/local/bin/scripts/data/video/*
```

## dependencies

* python 3.* (preinstalled)
* fswebcam (apt-get) - handling the webcam
* imagemagick (apt-get) - image manipulation
* libatlas-base-dev (apt-get) - ???
* pytz (pip) - python: time zones
* tweepy (pip) - python: twitter client
* foursquare (pip) - python: foursquare/swarm client
* numpy (pip) - twitter: library to handle numbers
* seaborn (pip) - twitter: library to visualise numbers (heatmaps here)
* space mono ([github.com/../spacemono](https://github.com/googlefonts/spacemono)) - font used to annotate timelapse frames
