#!/usr/bin/env bash

set -eux

#if [ "$1" = "/opt/keycloak/bin/kc.sh" ]; then
#	/opt/keycloak/bin/kc.sh import --file /import/realm-export.json
#fi

exec "$@"
