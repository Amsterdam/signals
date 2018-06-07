Download relevant data for Signals API
=================================================

author: Stephan Preeker.

About
------

- load wfs data into database, for now buurten.


Instructions
------------

::
        docker-compose up database

        pip install -r requirements.txt

# now you can run:

::
        # importeer buurt informatie.
        dc run --rm importer python load_wfs_postgres.py https://map.data.amsterdam.nl/maps/gebieden buurt_simple,stadsdeel 4326
