kriek
=====

Kriek is the easiest to use brewing control software for the raspberry pi.

Requirements
------------

A Raspberry Pi or BeagleBone Black.
DS18B20 temperature probes.
Solid State Relays.


Screen Shot
-----------
![main screen](screenshots/main.png)

Installation
------------

### By hand installation ###

These instructions assume a debian-based (JESSIE) install (raspbian, ubuntu, etc) on the pi or BBB.

**Debian Setup**
* sudo apt-get update
* sudo apt-get upgrade -y
* sudo apt-get install libpq-dev python-dev postgresql postgresql-client nginx supervisor python-virtualenv -y --force-yes

**For BBB**
* sudo apt-get install build-essential python-setuptools python-pip python-smbus -y

**Create a virutalenv for kriek**

* sudo mkdir /opt/kriek
* sudo chown pi /opt/kriek
* virtualenv /opt/kriek/env-kriek

**clone the source code**

* cd /opt/kriek/
* git clone https://github.com/jsproull/kriek.git


**pip requirements**
* /opt/kriek/env-kriek/bin/pip install -r /opt/kriek/kriek/requirements.txt

**We use either wiringpi or Adafruit_BBIO depending on the platform**

**for Pi**

* /opt/kriek/env-kriek/bin/pip install wiringpi

**for BBB**

* /opt/kriek/env-kriek/bin/pip install Adafruit_BBIO

**Configure postgres**
* sudo su postgres -c /opt/kriek/kriek/shell/psql.sh

**Configure the django kriek installation**

* cd /opt/kriek/kriek
* ./manage.py syncdb  --noinput
* echo "from django.contrib.auth.models import User; User.objects.create_superuser('pi', 'pi@example.com', 'pi')" | ./manage.py shell
* sudo ./manage.py collectstatic

**then set up gunicorn, supervisord and nginx**

* sudo rm /etc/nginx/sites-enabled/default
* sudo cp -R /opt/kriek/kriek/conf/ngnix/* /etc/nginx/
* sudo cp -R /opt/kriek/kriek/conf/supervisor/conf.d/* /etc/supervisor/conf.d/

**And set up the required modules**

**For Pi**

* sudo sh -c "echo '#one wire\ndtoverlay=w1-gpio\n' >> /boot/config.txt"

### Automatic installation ###

* sh < <(curl -s "https://raw.githubusercontent.com/jsproull/kriek/master/shell/install.sh”)

### Common part for both methods ###

**For BBB**

**TODO**

**Reboot**

sudo reboot

Once rebooted, you should be able to go to http://yourip and sign in using username: **pi** with password: **pi**

**Configuration**
-------------

**Coming soon**

