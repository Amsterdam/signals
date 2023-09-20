# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from signals.celery import app as celery_app

VERSION = (2, 31, '0-beta.1')
__version__ = '.'.join(str(part) for part in VERSION)
__all__ = ['celery_app', 'VERSION', '__version__', ]
