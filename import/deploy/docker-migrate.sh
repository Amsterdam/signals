#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

cd /app/

yes yes | python manage.py migrate --noinput

