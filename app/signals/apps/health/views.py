# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging

from django.db import Error, connections
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def health(request):
    try:
        connections['default'].cursor()
        return HttpResponse('Connectivity OK', content_type='text/plain', status=200)
    except Error as e:
        logging.error(e)
        return HttpResponse('Database connectivity failed', content_type='text/plain', status=500)
