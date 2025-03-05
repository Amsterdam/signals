#!/usr/bin/env bash
docker compose exec keycloak /opt/keycloak/bin/kc.sh export --realm signals --file /import/realm-export.json
