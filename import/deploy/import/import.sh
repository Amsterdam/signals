#!/bin/sh

set -e
set -u
set -x

DIR="$(dirname $0)"

dc() {
	docker-compose -p scrapebammens${ENVIRONMENT} -f ${DIR}/docker-compose.yml $*
}

trap 'dc kill ; dc rm -f' EXIT

# For database backups:
rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

echo "For debugging list volumes"
dc down	-v
dc rm -f
dc pull

echo "Building images"
dc build

echo "Bringing up and waiting for database"
dc up -d database
dc run importer /app/deploy/docker-wait.sh

# dc exec -T database update-table.sh bag bag_buurt public afvalcontainers

echo "Importing data into database"

dc run --rm api python manage.py migrate
# dc run --rm importer python models.py

# importeer buurt informatie.
dc run --rm importer python load_wfs_postgres.py https://map.data.amsterdam.nl/maps/gebieden buurt_simple,stadsdeel 4326

echo "Running backups"
dc exec -T database backup-db.sh signals

echo "Remove containers and volumes."
dc down -v
dc rm -f

echo "Done"
