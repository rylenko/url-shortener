#!/bin/sh

mkdir -p /usr/src/app/logs/

while true; do
	alembic upgrade head && break
	echo "Database upgrade failed, retrying in 5 seconds..."
	sleep 5
done

exec supervisord -n
