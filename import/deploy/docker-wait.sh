#!/usr/bin/env bash

set -u
set -e

# wait for postgres
while ! nc -z database 5432
do
	echo "Waiting for postgres..."
	sleep 2
done
