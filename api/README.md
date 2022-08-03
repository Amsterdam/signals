Signals
=======

Provides API services with signals data.


Project structure
=================

```
/app                   Docker mount /app
    /signals           Django root
        apps           Django apps
            health
            signals    (SIA core)
            ...
        settings
            __init__.py
            base.py
        urls.py
        wsgi.py
        ...
    /tests             All tests
        ...
    manage.py
    tox.ini
/deploy                Docker mount /deploy
```


Django settings
===============

Settings are defined in `app/signals/settings/...`. The file `base.py` contains all settings. Defaults should be 
production ready. 

Settings location:
```
/app
    /signals
        settings
            __init__.py
            base.py
```

You can override the settings, if needed, in the docker-compose.yml file. When not using docker-compose make sure to set
the environment variables (see the docker-compose.yml file for reference when setting these environment variables).

Example docker-compose.yml api setup:
```yaml
  api:
    build: ./api
    ports:
      - "8000:8000"
    links:
      - database
      - elasticsearch
      - dex
      - celery
    environment:
      - DEBUG=True
      - LOGGING_LEVEL=DEBUG
      - SITE_DOMAIN=localhost:8000
      - SECRET_KEY=insecure
      ...
    volumes:
      - ./api/app:/app
      - ./api/deploy:/deploy
      - ./dwh_media:/dwh_media
      - ./scripts/initialize.sh:/initialize.sh
    command:
      - /initialize.sh

```


Tox usage
=========

You can use tox to run all QA tests with one command. This is also used by Jenkins to run the 
`Test` pipeline. Tox is directly available in the Docker container. 

Tox runs:
- unit tests (with `pytest`)
- flake8 (pep8 checker)
- isort (import sorting)

##  Local usage

    $ cd api/app
    $ tox

    $ tox -e test
    $ tox -e flake8
    $ tox -e isort

    $ tox -e test -- -k specific_test


Docker Installation
===================

::
   docker-compose build
   docker-compose up


Manual Installation
===================


 1. Create a signals database.

 2. Add the postgis extension

::
    CREATE EXTENSION postgis;

Create the tables
=================

::
    python3 manage.py migrate

Load the data
=============

::
    docker-compose database update-db.sh signals


remove old geoviews:

::
    python manage.py migrate geo_views zero

create geoviews:

::

    python manage.py migrate geo_view

test
