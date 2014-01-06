#!/bin/bash

echo this will drop everything! are you sureee?
read

#for name in ferm brew status common; do
#  ./manage.py sqlclear $name | ./manage.py dbshell
#done

psql  -d raspbrew -c "drop schema public cascade; create schema public;"
./manage.py syncdb
