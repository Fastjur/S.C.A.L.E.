#!/bin/sh

echo "${0}: running migrations..."
python3.11 manage.py migrate --no-input || exit 1
#python3.11 manage.py collectstatic --no-input || exit 1

exec "$@"
