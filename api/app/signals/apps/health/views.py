# import json
import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import Error, connection
from django.http import HttpResponse

from signals.apps.signals.models import Category

# import os


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

# def _count_categories(health_objects, minimum_count=1):
#     """
#     Simple count to check if there are at least 'minimum_count' of objects in the table
#
#     :param health_objects:
#     :param minimum_count:
#     :return:
#     """
#     if health_objects.count() < minimum_count:
#         error_msg = 'Too few items in the database'
#         logger.error(error_msg)
#         raise Exception(error_msg)
#
#
# def _check_fixture_exists_in_db(health_model, data_to_check):
#     """
#     Will check if the data_to_check exists in the database using the health_model
#
#     :param health_model:
#     :param data_to_check:
#     :return:
#     """
#     try:
#         health_model.objects.get(**data_to_check)
#     except health_model.DoesNotExist:
#         error_msg = '{} data does not match fixture data'.format(health_model.__class__)
#         logger.error(error_msg)
#         raise Exception(error_msg)
#
#
# def _prepare_data_to_check(data_to_check):
#     """
#     Prepare the data from the fixture so that we can check if it exists in the database
#
#     :param data_to_check:
#     :return prepared_data_to_check:
#     """
#     prepared_data_to_check = data_to_check['fields'].copy()
#     for key in data_to_check['fields'].keys():
#         if isinstance(prepared_data_to_check[key], list):
#             prepared_data_to_check.pop(key)
#     return prepared_data_to_check


def check_categories(request):
    """
    Check if the categories are ok

    Example:

    The following fixture must exist in the database. The departments will not be included in the
    check for now. Also the PK does not matter, the fields are most important because they define
    the category and cannot change (yet).

    {
      "model": "signals.category",
      "pk": 1,
      "fields": {
        "main_category": 1,
        "slug": "veeg-zwerfvuil",
        "name": "Veeg- / zwerfvuil",
        "handling": "A3DEC",
        "departments": [
          4,
          6,
          12
        ]
      }
    },

    :param request:
    :return HttpResponse:
    """

    """
        SIG-1014 Aanpassen categorieen

        Because of the introduction of new categories, and the soft delete of other categories we
        decided to temporary disabled the code of the health check.

        The code will now always return a 200 "Data OK Category"

        TODO: Refactor the category health check into a proper reusable solution
    """
    #
    # models = {
    #     'signals.category': Category,
    # }
    #
    # try:
    #     _count_categories(Category.objects.filter(parent__isnull=False),
    #                       minimum_count=settings.HEALTH_DATA_SUB_CATEGORY_MINIMUM_COUNT)
    #
    #     _count_categories(Category.objects.filter(parent__isnull=True),
    #                       minimum_count=settings.HEALTH_DATA_MAIN_CATEGORY_MINIMUM_COUNT)
    #
    #     fixture_file = os.path.join(
    #         os.path.dirname(os.path.dirname(settings.BASE_DIR)),
    #         'app/signals/apps/signals/fixtures/categories.json'
    #     )
    #
    #     with open(fixture_file) as f:
    #         fixture_data = json.load(f)
    #
    #     for fixture in fixture_data:
    #         model_str = fixture['model']
    #         if model_str in models:
    #             model = models[model_str]
    #             data_to_check = _prepare_data_to_check(data_to_check=fixture)
    #             _check_fixture_exists_in_db(model, data_to_check)
    #
    # except Exception as e:
    #     return HttpResponse(e, content_type='text/plain', status=500)

    return HttpResponse(
        'Data OK {}'.format(Category.__name__),
        content_type='text/plain', status=200
    )
