# Signalen Informatievoorziening Amsterdam (SIA)
SIA can be used by citizens and interested parties to inform the Amsterdam
municipality of problems in public spaces (like noise complaints,
broken street lights etc.) These signals (signalen in Dutch) are then followed
up on by the appropriate municipal services.

The code for the associated web front-end is available from:
- https://github.com/Amsterdam/signals-frontend

SIA will replace MORA and is based on a proof of concept (https://github.com/Amsterdam/sia)
which ran on https://vaarwatermeldingen.amsterdam.nl/


## Project structure
This project is setup such that it can be built and run using Docker with minimal
effort. The root directory therefore contains some Docker prerequisites and documentation.
The actual Django application is present in the `/api/app` directory. The Django project
structure is documented in `/api/README.md`.


## Documentation
- [Application design](docs/application-design.md) 
- [API design](docs/api-design.md) 
- [Future integration with VNG ZDS 2.0](docs/ZDS/SIA-to-ZRC.md) **(subject to internal review)**


## Running using Docker for local development
### Prerequisites
* Git
* Docker


### Building the Docker images
Pull the relevant images and build the services:
```
docker-compose pull
docker-compose build
```


### Running the test suite and style checks
Start the Postgres database and Rabbit MQ services in the background, then run the test
suite (we use Pytest as test runner, the tests themselves are Django unittest style):
```
docker-compose up -d database rabbit
docker-compose run --rm api tox -e pytest -- -n0 -s
```

Our build pipeline checks that the full test suite runs successfully, that the style
checks are passed, and that test code coverage is high enough. All these checks can
be replicated locally by running Tox.
```
docker-compose run --rm api tox
```

During development make sure that the Tox checks succeed before putting in a pull
request, as any failed checks will abort the build pipeline.


### Running and developing locally using Docker and docker-compose
Assuming no services are running, start the database and queue:
```
docker-compose up -d database rabbit
```

Migrate the database:
```
docker-compose run --rm api python manage.py migrate
```

Start the Signals web application:
```
docker-compose up
```

You will now have the Signals API running on http://localhost:8000/signals/ .

The docker-compose.yml file that is provided mounts the application source in the
running `api` container, where UWSGI is set up to automatically reload the source.
This means that you can edit the application source on the host system and see the
results reflected in the running application immediately, i.e. without rebuilding
the `api` service.


## Other topics
### Celery

We use celery for sending e-mails. That also requires a rabbitmq instance.

To start celery for testing we need to have SMTP settings in celery:

::

    export EMAIL_HOST=smtp.gmail.com
    export EMAIL_HOST_USER=<gmail_account>
    export EMAIL_HOST_PASSWORD=<gmail_password>
    export EMAIL_PORT=465
    export EMAIL_USE_SSL=True
    export EMAIL_USE_TLS=False

    celery -A signals worker -l info


RabbitMQ is run from a docker instance.  In order to be able to use it we need to specify 
at startup the signals user and password and a vhost.

This is most easily using the default docker rabbitmq:3 and environment variables :

::

     - RABBITMQ_ERLANG_COOKIE='secret cookie here'
     - RABBITMQ_DEFAULT_USER=signals
     - RABBITMQ_DEFAULT_PASS=insecure
     - RABBITMQ_DEFAULT_VHOST=vhost

Otherwise we need to add a user with:

::

    docker-compose exec rabbit rabbitmqctl add_user signals insecure
    docker-compose exec rabbit rabbitmqctl add_vhost vhost
    docker-compose exec rabbit rabbitmqctl set_permissions -p rabbitmq_signals signals ".*" ".*" ".*"

...

### Authentication 

Authentication can be done with the Authz service with either the _datapunt_ or the _grip_ Idp.

Users that have a ADW account should login with the grip Idp. They will get a prompt from the 
GRIP KPN login page and login with their username (6 letters and 3 digits) and their ADW password. 

In order to be authorized  for the Signals application their account should exist also the Django Admin
user administration below. There groups and superuser status can be set. 

Users that do not have a ADW account should  be added both to the Datapunt Idp and the authz_admin service 
as described in _https://dokuwiki.datapunt.amsterdam.nl/doku.php?id=start:aa:useraccounts_ and
_https://dokuwiki.datapunt.amsterdam.nl/doku.php?id=start:aa:userpermissions_

These accounts should be given the Signals Admin role

This is normally done by Service and Delivery. 

In addition the account should then also be created in the Django Admin below. 

NOTE : We should use e-mail addresses always in lowercase because some services 
are case sensitive , and then it looks like users do not exist. 



### Django Admin for user maintenance

To maintain user and groups we use Django Admin. We cannot yet login to Djang Admin with JWT tokens 
so for  now we need to set  a password for a staff account.  This is needed to login to Django Admin:


This can be set the following commands. On acception or production you have to
login to the Docker host computer and become root.

Then execute : 

`docker exec -it signals python manage.py changepassword signals.admin@example.com `

and set the password. 

If the user does not yest exist, you can create it by executing :

`docker exec -it signals python manage.py createsuperuser --username  signals.admin@example.com --email signals.admin@example.com
`

and then setting the password.


Then you can go to either : 

`https://acc.api.data.amsterdam.nl/signals/admin/`

or

`https://api.data.amsterdam.nl/signals/admin/`

and login with credentials just created. Note: these URLs are not exposed
publicly.

In order to create some default groups for signals you have to run:

`docker exec -it signals python manage.py create_groups`

We can also import a CSV file with users. It should look like :

~~~~
user_email,groups,departments,superuser,staff,action
signals.monitor@example.com,monitors,,false,false,
signals.behandelaar@example.com,behandelaars,,false,false,
signals.coordinator@example.com,coordinatoren,,false,false,
user.todelete@amsterdam,,,,,delete
... 
~~~~  


First copy the file to the server :

`scp users.csv <servername>:/tmp/users.csv`

The on that server copy it to the docker instance :

`docker cp /tmp/users.csv signals:/tmp/users.csv`

Then import the file with : 

`docker exec -it signals python manage.py create_users /tmp/users.csv`

This should create users in the CSV file. It does NOT overwrite passwords.
