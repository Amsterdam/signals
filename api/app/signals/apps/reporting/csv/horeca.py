import csv
import logging
import os
import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from signals.apps.reporting.app_settings import CSV_BATCH_SIZE as BATCH_SIZE
from signals.apps.reporting.csv.utils import _get_storage_backend
from signals.apps.signals.models import Category, Signal

logger = logging.getLogger(__name__)


def get_swift_parameters():
    """Get Swift parameters for 'Horeca data levering'"""
    return {
        'api_auth_url': settings.HORECA_SWIFT_AUTH_URL,
        'api_username': settings.HORECA_SWIFT_USERNAME,
        'api_key': settings.HORECA_SWIFT_PASSWORD,
        'tenant_name': settings.HORECA_SWIFT_TENANT_NAME,
        'tenant_id': settings.HORECA_SWIFT_TENANT_ID,
        'region_name': settings.HORECA_SWIFT_REGION_NAME,
        'container_name': settings.HORECA_SWIFT_CONTAINER_NAME,
        'auto_overwrite': True,
    }


def _to_first_and_last_day_of_the_week(isoweek, isoyear):
    first_day_of_week = timezone.datetime.strptime(
        '{}-W{}-1'.format(isoyear, isoweek), '%G-W%V-%u'
    )
    last_day_of_week = first_day_of_week + timedelta(days=7)
    return first_day_of_week, last_day_of_week


def _fix_row_to_match_header_count(row, headers):
    return row + ([None] * (len(headers) - len(row)))


def _fix_rows_to_match_header_count(rows, headers):
    return [
        _fix_row_to_match_header_count(row, headers)
        for row in rows
    ]


def _create_extra_properties_headers(extra_properties, headers=None):
    """
    We want the extra_properties to be in one of the following formats

    [
        {
            'id': 'Lorem',
            'label': 'ipsum',
            'answer': 'the answer',
            'category_url': '/signals/v1/public/terms/categories/X/sub_categories/Y'
        },
        ...
    ]

    or

    [
        {
            'id': 'Lorem',
            'label': 'ipsum',
            'answer': {
                'value': 'the answer'
            },
            'category_url': '/signals/v1/public/terms/categories/X/sub_categories/Y'
        },
        ...
    ]

    The old style extra_properties will be ignored

    {
        'question_1': 'answer_1',
        'question_2': 'answer_2',
        'question_3': 'answer_3',
        ...
    }
    """
    headers = headers or []

    if extra_properties:
        for extra_property in extra_properties:
            if isinstance(extra_property, str):
                continue  # old style, we ignore these

            if extra_property['id'] not in headers:
                headers.append(extra_property['id'])

    return headers


def _create_extra_properties_row(extra_properties, headers):
    """
    We want the extra_properties to be in one of the following formats

    [
        {
            'id': 'Lorem',
            'label': 'ipsum',
            'answer': 'the answer',
            'category_url': '/signals/v1/public/terms/categories/X/sub_categories/Y'
        },
        ...
    ]

    or

    [
        {
            'id': 'Lorem',
            'label': 'ipsum',
            'answer': {
                'value': 'the answer'
            },
            'category_url': '/signals/v1/public/terms/categories/X/sub_categories/Y'
        },
        ...
    ]

    The old style extra_properties will be ignored

    {
        'question_1': 'answer_1',
        'question_2': 'answer_2',
        'question_3': 'answer_3',
        ...
    }
    """
    row = [None] * len(headers)

    if extra_properties:
        for extra_property in extra_properties:
            if isinstance(extra_property, str):
                continue  # old style, we ignore these

            answer = None
            if isinstance(extra_property['answer'], str):
                answer = extra_property['answer']
            elif 'value' in extra_property['answer']:
                answer = extra_property['answer']['value']
            row[headers.index(extra_property['id'])] = answer

    return row


def _get_horeca_main_category():
    return Category.objects.get(slug='overlast-bedrijven-en-horeca', parent_id__isnull=True)


def _get_csv_rows_per_category(category, created_at__range):
    headers = []
    rows = []

    qs = Signal.objects.filter(category_assignment__category_id=category.pk,
                               created_at__range=created_at__range)

    for signal in qs.iterator(chunk_size=BATCH_SIZE):
        headers = _create_extra_properties_headers(signal.extra_properties, headers)
        rows.append([
            signal.pk,
            signal.signal_id,
            signal.source,
            signal.text,
            signal.text_extra,
            signal.incident_date_start,
            signal.incident_date_end,
            signal.created_at,
            signal.updated_at,
            signal.operational_date,
            signal.expire_date,
            signal.upload,
            signal.category_assignment_id,
            signal.location_id,
            signal.reporter_id,
            signal.status_id,
        ] + _create_extra_properties_row(signal.extra_properties, headers))

    headers = [
        'id',
        'signal_uuid',
        'source',
        'text',
        'text_extra',
        'incident_date_start',
        'incident_date_end',
        'created_at',
        'updated_at',
        'operational_date',
        'expire_date',
        'upload',
        'category_assignment_id',
        'location_id',
        'reporter_id',
        'status_id',
    ] + headers

    return [headers, ] + _fix_rows_to_match_header_count(rows, headers)


def create_csv_per_sub_category(category, location, isoweek, isoyear):
    now = timezone.now()

    if category.is_parent():
        raise ValidationError(
            'Function \'create_csv_per_sub_category\' can only work with sub categories'
        )

    parent_category = _get_horeca_main_category()
    if category.parent_id != parent_category.pk:
        raise NotImplementedError(f'Not implemented for categories that do not belong to the main '
                                  f'category ({parent_category.name})')

    first_day_of_week, last_day_of_week = _to_first_and_last_day_of_the_week(isoweek, isoyear)
    rows = _get_csv_rows_per_category(category, created_at__range=(first_day_of_week,
                                                                   last_day_of_week))

    file_name = 'signals_{}_{}.csv'.format(category.slug, now.strftime('%d-%m-%Y_%H_%M_%S'))
    logger.debug('Writing to: {}'.format(os.path.join(location, file_name)))

    with open(os.path.join(location, file_name), 'w') as csv_file:
        writer = csv.writer(csv_file)
        for row in rows:
            writer.writerow(row)

    return csv_file.name


def create_csv_files(isoweek, isoyear, save_in_dir=None):
    category = _get_horeca_main_category()

    csv_files = []

    # TODO: Change the way we store/serve these csv files in the next ticket. SIG-1547 is only about
    #       generating the CSV files and the content. So for now we store them in a "temporary"
    #       directory

    with tempfile.TemporaryDirectory() as tmp_dir:
        for sub_category in category.children.all():
            csv_file = create_csv_per_sub_category(
                sub_category, tmp_dir, isoweek=isoweek, isoyear=isoyear
            )
            csv_files.append(csv_file)

        if save_in_dir:
            for csv_file in csv_files:
                logger.info('Copy file "{}" to "{}"'.format(csv_file, save_in_dir))
                shutil.copy(csv_file, save_in_dir)
        elif os.getenv('SWIFT_ENABLED', 'false') == 'true':
            storage = _get_storage_backend(get_swift_parameters())
            for csv_file_path in csv_files:
                with open(csv_file_path, 'rb') as opened_csv_file:
                    file_name = os.path.basename(opened_csv_file.name)
                    storage.save(name=file_name, content=opened_csv_file)

    return csv_files
