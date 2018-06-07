Signals
=============


provides API and WFS services with signals data

- all signals.

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
