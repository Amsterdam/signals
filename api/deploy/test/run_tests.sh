#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

cd /app
export COVERAGE_FILE=/tmp/.coverage
source /deploy/docker-wait.sh
tox
