import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import Error, connection
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('select 1')
            assert cursor.fetchone()
    except Error:
        error_msg = 'Database connectivity failed'
        logger.exception(error_msg)
        return HttpResponse(error_msg, content_type='text/plain', status=500)
    else:
        return HttpResponse('Connectivity OK', content_type='text/plain', status=200)


def check_data(request):
    try:
        health_check_model = apps.get_model(settings.HEALTH_MODEL)
    except LookupError:
        raise ImproperlyConfigured('`settings.HEALTH_MODEL` does not resolve to a usable model')

    count = health_check_model.objects.count()
    if count < 2:
        logger.error('Too few items in the database')
        return HttpResponse('Too few items in the database', content_type='text/plain', status=500)

    return HttpResponse(f'Data OK {count} {health_check_model.__name__}', content_type='text/plain', status=200)
