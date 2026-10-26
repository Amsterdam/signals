# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2025 Gemeente Amsterdam
import os

from signals.celery import app as celery_app

VERSION = os.environ["VERSION"]
__version__ = VERSION if VERSION is not None else "0.0.0"
__all__ = [
    "VERSION",
    "__version__",
    "celery_app",
]
