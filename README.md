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

*Also see the section "Authentication for local development" below.*

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
The Django Debug Toolbar is enabled when running with local development settings.

The docker-compose.yml file that is provided mounts the application source in the
running `api` container, where UWSGI is set up to automatically reload the source.
This means that you can edit the application source on the host system and see the
results reflected in the running application immediately, i.e. without rebuilding
the `api` service.

#### Connecting to the database directly
After the Signals application is running, find the docker `CONTAINER ID` of the
PostgreSQL database:
```
docker ps
```

Using the `CONTAINER ID` associated with `signals_database_1`, use
`docker exec` to start a bash shell in the database context.
(In this example the id used is `21f3acd89dd7`):
```
docker exec -it 21f3acd89dd7 bash
```

From the shell prompt, connect to the database using the PostgreSQL commandline
client:
```
psql --user=signals --port=5432
```

You will now be able to explore the database schema and data using SQL.

## Other topics
### Authentication and Authorization

Authentication and authorization are split up for the SIA project. Authentication
is performed through OAuth2 using JWT tokens and the authorization is managed
using standard Django users, groups and permissions.

SIA makes some assumptions about OAuth2 authentication:
- SIA is looking for the 'SIG/ALL' role
- SIA uses email addresses as usernames (all lower case)

SIA authorizes users if:
- there is a known Django user with a matching username
- that Django user has the correct user Django permissions

NOTE : We should use e-mail addresses always in lowercase because some services 
are case sensitive, and then it looks like users do not exist. 


### Managing SIA users

To maintain users and groups we use Django Admin. We cannot login to the Django
Admin with JWT tokens so for now we need to set a password for a staff account.


### Authentication for local development

Since a developer setup may not have a local OAuth2 setup to which SIA can
connect. To bypass OAuth for local development the `docker-compose.yml` file
in the project root and the `development.py` Django settings file are 
pre-configured to authenticate a special user (configurable see the `TEST_LOGIN`
setting variable) is authenticated. Make sure that this special user is also
present in Django (as a superuser).

The default development configuration for SIA uses `signals.admin@example.com`
as the user name. To add this user to the SIA Django application running 
under `docker-compose`:
```
docker-compose run --rm api python manage.py createsuperuser --username signals.admin@example.com --email signals.admin@example.com
```
