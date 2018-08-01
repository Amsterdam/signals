#!/bin/sh

set -e
set -u
set -x

DIR="$(dirname $0)"

dc() {
	docker-compose -p signaltest -f ${DIR}/docker-compose.yml $*
}


dc stop
dc rm --force
dc down
dc pull
dc build

dc up -d database
dc up -d rabbit

dc run --rm tests

dc stop
dc rm --force
dc down
