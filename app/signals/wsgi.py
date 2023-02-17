# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'signals.settings')

application = get_wsgi_application()
