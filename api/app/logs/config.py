# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
BASE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'elaborate': {
            'format': '{levelname} {name} {module}.{filename} {message}',
            'style': '{'
        }
    },
    'filters': {
        'require_debug_queries': {
            '()': 'logs.filters.DebugQueryFilter'
        },
        'static_fields': {
            '()': 'logs.filters.StaticFieldFilter',
            'fields': {
                'project': 'SignalsAPI',
                'environment': 'Any',
                'hideme': 'True'
            },
        },
    },
    'handlers': {
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'colorize': {
            'class': 'logs.handlers.ColoredHandler',
            'formatter': 'elaborate'
        },
        'colorless': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'level': 'DEBUG',
            'handlers': ['colorless'],
        },
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['colorless'],
            'filters': ['require_debug_queries'],
            'propagate': False,
        },
        'django.utils.autoreload': {
            'level': 'ERROR',
            'propagate': False,
        }
    },
}
