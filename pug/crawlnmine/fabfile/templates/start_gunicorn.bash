#!/bin/bash
# Starts the Gunicorn server
set -e

# Activate the virtualenv for this project
%(ACTIVATE)s

# Start gunicorn going
exec gunicorn %(PROJECT_NAME)s.wsgi:application -c %(PROJECT_PATH)s/gunicorn.conf.py 