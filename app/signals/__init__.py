# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2025 Gemeente Amsterdam
from signals.celery import app as celery_app

VERSION = (2, 43, '8')
__version__ = '.'.join(str(part) for part in VERSION)
__all__ = ['celery_app', 'VERSION', '__version__', ]
