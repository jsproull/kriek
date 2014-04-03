#!/bin/sh

createdb kriek
echo "DROP user pi"
echo "CREATE user pi with password 'pi';GRANT ALL PRIVILEGES ON DATABASE kriek to pi;" | psql
