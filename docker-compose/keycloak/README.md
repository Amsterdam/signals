This provides a basic Keycloak setup that imports a preconfigured realm from `import/realm-export.json`.

By default, this is a realm named "signals", which contains a client that is also named "signals".
There currently is one user available with username "signals.admin@example.com" and email "signals.admin@example.com".
The password for this user is "password".

To change the configuration, please go to http://localhost:8002 and log in as administrator with username "admin" and
password "admin". Once you're satisfied with the changed configuration, please run:
```shell
docker-compose/keycloak/export-realm.sh
```
to export the changed configuration to `import/realm-export.json`, so that it can be imported on the next start of
Keycloak.
