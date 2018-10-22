# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from signals.celery import app as celery_app
from signals.utils.version import get_version

__all__ = ['celery_app', ]

VERSION = (0, 5, 0)  # Major, minor, patch

__version__ = get_version(VERSION)
