import os

from celery.schedules import crontab

from signals.settings.base import *  # noqa

from .zds import *  # noqa

SECRET_KEY = 'insecure'
DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATAPUNT_AUTHZ['ALWAYS_OK'] = True  # noqa
SITE_DOMAIN = 'localhost:8000'

INSTALLED_APPS += [  # noqa
    'debug_toolbar',
]
MIDDLEWARE.append(  # noqa
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEST_LOGIN = os.getenv('TEST_LOGIN', 'signals.admin@example.com')

IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'

# ML_TOOL_ENDPOINT = 'https://acc.api.data.amsterdam.nl/signals_mltool'

try:
    from signals.settings.local import *  # noqa
except ImportError:
    pass

CELERY_TASK_ALWAYS_EAGER = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'rebuild-elastic': {  # Run task every 3rd day of the week at midnight
        'task': 'signals.apps.search.tasks.rebuild_index',
        'schedule': crontab(minute='00', hour='00', day_of_week='3'),
    },
}


def show_toolbar(request):
    return False  # DEBUG


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

# Search settings
SEARCH = {
    'PAGE_SIZE': 500,
    'CONNECTION': {
        'URL': 'elasticsearch:9200',
        'INDEX': 'sia_signals',
    },
}
