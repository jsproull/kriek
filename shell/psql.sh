#!/bin/sh

createdb kriek
dropuser pi
createuser -s pi
echo "ALTER user pi with password 'pi'; GRANT ALL PRIVILEGES ON DATABASE kriek to pi;" | psql
