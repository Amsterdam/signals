#!/usr/bin/env bash

set -u
set -e

echo 0.0.0.0:5432:signals:signals:insecure > ~/.pgpass

chmod 600 ~/.pgpass

# dump occupation data
pg_dump  -t buurtcombinatie \
	 -t stadsdeel \
	 -Fc \
	 -U signals \
	 -h 0.0.0.0 -p 5432 \
	 -f /tmp/backups/importtables.dump \
	 signals
