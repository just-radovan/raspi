# raspi

various scripts to notify me about what's happening at home. via twitter.

## crontab

```
*	*	*	*	*	/usr/local/bin/scripts/ping_device.py >> /usr/local/bin/scripts/log/log
*/2	*	*	*	*	/usr/local/bin/scripts/check.py >> /usr/local/bin/scripts/log/log
*/1	*	*	*	*	/usr/local/bin/scripts/netatmo_download.py >> /usr/local/bin/scripts/log/log
*/3	*	*	*	*	/usr/local/bin/scripts/take_photo.py >> /usr/local/bin/scripts/log/log
10  23	*	*	*	/usr/local/bin/scripts/make_video.py >> /usr/local/bin/scripts/log/log
10	22	*	*	0	/usr/local/bin/scripts/presence_heatmap.py >> /usr/local/bin/scripts/log/log

0	0	*	*	*	cp /usr/local/bin/scripts/data/* /mnt/storage/backup/
```

## dependencies

* python 3.*
* fswebcam (apt-get)
* imagemagick (apt-get)
* libatlas-base-dev (apt-get)
* tweepy (pip)
* numpy (pip)
* seaborn (pip)
