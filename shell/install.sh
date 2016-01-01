#!/bin/sh

#
## initial install script.
## Only run on a stock raspbian install.
#

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install libpq-dev python-dev postgresql postgresql-client nginx supervisor python-virtualenv -y --force-yes

# for BBB
#sudo apt-get install build-essential python-setuptools python-pip python-smbus -y
# for bbb
#sudo adduser pi

# make our kriek directory
sudo mkdir /opt/kriek
sudo chown pi /opt/kriek

# set up a virtualenv
virtualenv /opt/kriek/env-kriek

#git
cd /opt/kriek
git clone https://github.com/jsproull/kriek.git

#pippy
/opt/kriek/env-kriek/bin/pip install -r /opt/kriek/kriek/requirements.txt

# for Pi
# install wiring pi
/opt/kriek/env-kriek/bin/pip install wiringpi

# for BBB
# /opt/kriek/env-kriek/bin/pip install Adafruit_BBIO

#conf postgres
sudo su postgres -c /opt/kriek/kriek/shell/psql.sh

#conf django
cd /opt/kriek/kriek
./manage.py syncdb  --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('pi', 'pi@example.com', 'pi')" | ./manage.py shell
sudo ./manage.py collectstatic --noinput

#then set up gunicorn, supervisord and nginx
sudo rm /etc/nginx/sites-enabled/default
sudo cp -R /opt/kriek/kriek/conf/ngnix/* /etc/nginx/
sudo cp -R /opt/kriek/kriek/conf/supervisor/conf.d/* /etc/supervisor/conf.d/

# raspberry pi modules
# sudo sh -c "echo 'w1_gpio\nw1_therm\n' >> /etc/modules"

#raspberry pi device tree
sudo sh -c "echo '#one wire\ndtoverlay=w1-gpio\n' >> /boot/config.txt"
