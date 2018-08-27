from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATAPUNT_AUTHZ['ALWAYS_OK'] = True  # noqa
TEST_LOGIN = 'signals.admin@amsterdam.nl'
