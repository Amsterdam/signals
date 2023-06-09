#!/usr/bin/env bash
set -eux

docker-compose up -d --build
docker-compose exec --user=root api apt-get update
docker-compose exec --user=root api apt-get install -yqq make
docker-compose exec --user=root api make install
