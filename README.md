# raspi

various scripts to notify me about what's happening at home. via twitter.

## crontab

```
*       *       *       *       *       /usr/local/bin/raspi/ping_device.py
*/2     *       *       *       *       /usr/local/bin/raspi/check.py
*/1     *       *       *       *       /usr/local/bin/raspi/netatmo_download.py
20      8-20/2  *       *       *       /usr/local/bin/raspi/check_cat_food.py
```

## dependencies

* python 3.*
* fswebcam (apt-get)
* tweepy (pip)
* numpy (pip)
* seaborn (pip)
