# Signalen Informatievoorziening Amsterdam (SIA)

SIA can be used by citizens and interested parties to inform the Amsterdam
municipality of problems in public spaces (like noise complaints,
broken street lights etc.) These signals (signalen in Dutch) are then followed
up on by the appropriate municipal services.

The code for the associated web front-end is available from 
[Amsterdam/signals-frontend](https://github.com/Amsterdam/signals-frontend).

SIA has replaced MORA and is based on a proof of concept (https://github.com/Amsterdam/sia)
which ran on https://vaarwatermeldingen.amsterdam.nl/

## Contributing to the project

Do you want to contribute? Take a look at our [contribution guide](docs/CONTRIBUTING.md).

## Project structure

This project is setup such that it can be built and run using Docker with minimal
effort. The root directory therefore contains some Docker prerequisites and documentation.
The actual Django application is present in the `/api/app` directory. The Django project
structure is documented in `/api/README.md`.

## Documentation

For in-depth technical documentation see the [documentation section](./docs).

## Running using Docker for local development

### Prerequisites

* Git
* Docker

### Building the Docker images

Pull the relevant images and build the services:

```console
docker-compose pull
docker-compose build
```

### Running the test suite and style checks

Start the Postgres database and Rabbit MQ services in the background, then run the test
suite (we use Pytest as test runner, the tests themselves are Django unittest style):

```console
docker-compose up -d database rabbit
docker-compose run --rm api tox -e pytest -- -n0 -s
```

Our build pipeline checks that the full test suite runs successfully, that the style
checks are passed, and that test code coverage is high enough. All these checks can
be replicated locally by running Tox.

```console
docker-compose run --rm api tox
```

During development make sure that the Tox checks succeed before putting in a pull
request, as any failed checks will abort the build pipeline.

*Also see the section "Authentication for local development" below.*

### Running and developing locally using Docker and docker-compose

Assuming no services are running, start the database and queue:

```console
docker-compose up -d database rabbit
```

Migrate the database:

```console
docker-compose run --rm api python manage.py migrate
```

Start the Signals web application:

```console
docker-compose up
```

You will now have the Signals API running on http://localhost:8000/signals/ .
The Django Debug Toolbar is enabled when running with local development settings.

The docker-compose.yml file that is provided mounts the application source in the
running `api` container, where UWSGI is set up to automatically reload the source.
This means that you can edit the application source on the host system and see the
results reflected in the running application immediately, i.e. without rebuilding
the `api` service.

## Authentication and authorization

The Signals backend authenticates users through an external OpenID Connect
provider. The backend performs a case-insensitive matches through the
`USER_ID_FIELD` (default: email) to match users. Users need to exist in the
database first before they are allowed to login. Permissions are also handled
in the backend.

### Local development

The Docker Compose file provides [Dex](https://github.com/dexidp/dex) as Identity
Provider.

Start Dex with the following command:

```console
docker-compose up -d dex
```

The data of Dex is persisted on a [named volume](https://docs.docker.com/storage/volumes/). The following user is created:

- E-mail: signals.admin@example.com
- Password: password

Request an access token through the following URL: http://localhost:5556/auth?response_type=id_token&scope=openid+email+profile&client_id=signals&redirect_uri=http://localhost:3001/manage/incidents&nonce=random-nonce

After login is completed, copy `access_token` from the URL you are redirected to. You
can use this token to make calls to the API.

Make sure you assign superuser permissions to the default user with:

```console
docker-compose run --rm api python manage.py createsuperuser --username signals.admin@example.com --email signals.admin@example.com
```
