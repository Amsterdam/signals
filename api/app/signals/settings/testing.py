from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
TEST_LOGIN = 'signals.admin@amsterdam.nl'
SITE_DOMAIN = 'localhost:8000'
