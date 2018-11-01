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
        raise ImproperlyConfigured(
            "`settings.HEALTH_MODEL` {} doesn't resolve to a useable model".format(
                settings.HEALTH_MODEL))

    count = health_check_model.objects.count()
    if count < 2:
        error_msg = 'Too few items in the database'
        logger.error(error_msg)
        return HttpResponse(error_msg, content_type='text/plain', status=500)

    return HttpResponse(
        'Data OK {count} {model}'.format(count=count, model=health_check_model.__name__),
        content_type='text/plain',
        status=200)


def _check_main_categories(request):
    health_model = 'signals.MainCategory'
    at_least_in_database = 1

    try:
        health_check_model = apps.get_model(health_model)
    except LookupError:
        raise ImproperlyConfigured(
            "{} doesn't resolve to a useable model".format(health_model))

    count = health_check_model.objects.count()
    if count < at_least_in_database:
        error_msg = 'Too few \'{}\' items in the database'.format(health_model)
        logger.error(error_msg)
        return HttpResponse(error_msg, content_type='text/plain', status=500)


def _check_sub_categories(request):
    health_model = 'signals.SubCategory'
    at_least_in_database = 1

    try:
        health_check_model = apps.get_model(health_model)
    except LookupError:
        raise ImproperlyConfigured(
            "{} doesn't resolve to a useable model".format(health_model))

    count = health_check_model.objects.count()
    if count < at_least_in_database:
        error_msg = 'Too few \'{}\' items in the database'.format(health_model)
        logger.error(error_msg)
        return HttpResponse(error_msg, content_type='text/plain', status=500)
