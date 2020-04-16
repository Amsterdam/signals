# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from signals.celery import app as celery_app
from signals.utils.version import get_version

__all__ = ['celery_app', 'VERSION', 'API_VERSIONS', ]

# Versioning
# ==========
#
# We are tracking multiple versions. First we've the application version which increments by every
# release. Based on the changes in the new release there is a major, minor or patch version bump.
#
# Besides that we've API versioning which are seperated versioning numbers for the given API. The
# major versioning number of the API is fixed related to the given API. e.g. API Version 1 with url
# `/signals/v1/...` will always have major API version number `1`.

# Application version (Major, minor, patch)
VERSION = (0, 15, 0)

# API versions (Major, minor, patch)
API_VERSIONS = {
    'v0': (0, 8, 0),
    'v1': (1, 12, 0),
}

__version__ = get_version(VERSION)
