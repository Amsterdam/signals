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
        settings.py
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

Settings for all different environments are defined in `app/signals/settings/...`. The file
`base.py` contains all the default settings. Defaults should be production ready. You can
override this, if needed, in one of the other specific settings files (e.g. `testing`).

Current available settings:

- `production`      -> Used for Acceptance/Production instances
- `testing`         -> Used for Jenkins test pipeline and testing with `tox`
- `development`     -> Used for Local Docker instances
- `local`           -> Override settings in `development` for local usage (not tracked in Git)


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
