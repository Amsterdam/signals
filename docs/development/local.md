# Local Development Guide
This guide explains how to set up and run the project locally using Docker for
local development.

## Prerequisites
Before starting with the setup, make sure the following are installed:

- Git
- Docker

## Cloning the repository
First, clone the repository:

```console
git clone https://github.com/Amsterdam/signals
```

## Building the Docker images
After cloning the repository, navigate to the root directory and pull the
relevant images and build the services:

```console
cd signals/
docker-compose pull
docker-compose build
```

## Running the application
### Starting the Signals API
Start the api:

```console
docker-compose up -d
```

You will now have the Signals API running on http://localhost:8000/signals/.

In the docker-compose.yml file, the command section under the api service
specifies that the container should run the
[/initialize.sh](../../docker-compose/scripts/initialize.sh) script. This script
is responsible for running all the basic setup required for the application to
work properly.

In this particular case, the initialize.sh script is used for the following:

- Recreate the database when the INITIALIZE_WITH_DUMMY_DATA env variable is set
- Running all migrations
- Making sure that the superuser exists
- Running the collectstatic command
- Loading dummy data when the INITIALIZE_WITH_DUMMY_DATA env variable is set
- Running the UWSGI command, UWSGI is set up to automatically reload the source.
This means that you can edit the application source on the host system and see
the results reflected in the running application immediately, i.e. without
rebuilding the `api` service.

### Docker Compose Environment Variables
The environment variables used by the services are defined in files located in
the `docker-compose/environments/` directory. For example, the api service uses
environment variables defined in the [.api](../../docker-compose/environments/.api)
file.

To modify the environment variables used by a service, you can edit the
corresponding file in the docker-compose/environments/ directory. Note that
changes to these files will only take effect when the Docker Compose containers
are recreated.

You can view the environment variables used by a running container by running
the following command:

```console
docker-compose exec api env
```

## Authentication and authorization
The Signals backend authenticates users through an external OpenID Connect
provider. The backend performs a case-insensitive match through the
USER_ID_FIELDS (default: "email") to match users. Users need to exist in the
database first before they are allowed to log in. Permissions are also handled
in the backend.

The Docker Compose file provides [Dex](https://github.com/dexidp/dex) as
Identity Provider.

The data of Dex is persisted on a [named volume](https://docs.docker.com/storage/volumes/).

The following user is created:

- E-mail: signals.admin@example.com
- Password: password

Request an access token through the following URL: http://localhost:5556/auth?response_type=id_token&scope=openid+email+profile&client_id=signals&redirect_uri=http://localhost:3001/manage/incidents&nonce=random-nonce

After login is completed, copy `access_token` from the URL you are redirected
to. You can use this token to make calls to the API.


## Running the test suite and style checks
When developing you may want to run the test suite and style checks from time
to time. Run the test suite:

```console
docker-compose -f docker-compose.test.yaml run --rm api tox
```

Or if you only want to run a specific test or tests:

```console
docker-compose -f docker-compose.test.yaml run --rm api tox -e pytest signals/apps/api/tests/test_get_root.py -- -n0
```

**Make sure to check if the Tox checks succeed before submitting a pull request.**

## Profiling with Django Silk
Django Silk is a profiling tool for Django web applications. It provides
detailed information about the performance of your views and SQL queries, among
other things.

### Configuration
By default, Django Silk is **disabled** in the project.

To enable Django Silk, you need to set the `SILK_ENABLED` environment variable
to a truthy value (`True`, `true`, `1`).

If you want to enable Python profiling, you can set the `SILK_PROFILING_ENABLED`
environment variable to a truthy value.

To enable authentication and authorization for accessing the Django Silk
reports, you can set the `SILK_AUTHENTICATION_ENABLED` environment variable to a
truthy value.

You can set these environment variables in your Docker Compose configuration
file. You can change them in the [.api](../../docker-compose/environments/.api)
file like this:

```
SILK_ENABLED=True
SILK_PROFILING_ENABLED=True
SILK_AUTHENTICATION_ENABLED=True
```

Note that if you enable authentication and authorization, you will need to log
in to the Django admin interface as a superuser before you can access the Django
Silk reports.

### Usage
Once Django Silk is configured, you can access the profiling reports by
navigating to the `/silk/` URL in your browser. This will display a list of all
the requests that Django Silk has recorded.

To view the details of a particular request, click on the request's URL. This
will show you a detailed report that includes information about the view
function, SQL queries, templates, and more.

You can also use Django Silk's API to record additional requests or to customize
the way requests are recorded. For more information, see the Django Silk
[documentation](https://github.com/jazzband/django-silk).

That's it! With Django Silk, you can profile and identify performance
bottlenecks.

## Mail
To test mail during development [Mailpit](https://github.com/axllent/mailpit) is
available. Its SMTP server is listening on tcp port 1025 and the web interface is
available on [http://localhost:8025](http://localhost:8025).
