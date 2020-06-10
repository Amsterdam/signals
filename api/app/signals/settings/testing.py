from signals.settings.base import *  # noqa

SECRET_KEY = 'insecure'
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
TEST_LOGIN = 'signals.admin@example.com'
SITE_DOMAIN = 'localhost:8000'
INSTALLED_APPS += [  # noqa
    'change_log.tests',  # Added so that we can test the chane_log with a "test only" model
]

SIGNALS_AUTHZ = {
    'JWKS': JWKS_TEST_KEY,  # noqa
    'ALWAYS_OK': True,
    'USER_ID_FIELD': 'sub'
}
# Email integration settings
EMAIL_INTEGRATIONS = dict(
    FLEX_HORECA=dict(
        RECIPIENT_LIST=['test@test.com', ],
        APPLICABLE_RULES=dict(
            WEEKDAYS='5,6,7',  # fri, sat, sun
            END_TIME='04:00',  # 04:00 o'clock
        )
    ),
    TOEZICHT_OR_NIEUW_WEST=dict(
        RECIPIENT_LIST=['test@test.com', ],
    ),
    VTH_NIEUW_WEST=dict(
        RECIPIENT_LIST=['test@test.com', ],
    ),
)

FEATURE_FLAGS['API_SEARCH_ENABLED'] = False  # noqa F405
FEATURE_FLAGS['SEARCH_BUILD_INDEX'] = False  # noqa F405
