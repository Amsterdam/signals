#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

cd /app
source /deploy/docker-wait.sh
python manage.py test --noinput
