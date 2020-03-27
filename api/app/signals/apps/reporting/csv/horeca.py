import csv
import logging
import os
import shutil
import tempfile
import time
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils import timezone

from signals.apps.reporting.app_settings import CSV_BATCH_SIZE as BATCH_SIZE
from signals.apps.reporting.models.export import HorecaCSVExport
from signals.apps.signals.models import Category, Signal

logger = logging.getLogger(__name__)


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
            elif 'label' in extra_property['answer']:
                answer = extra_property['answer']['label']
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
            signal.location.stadsdeel if signal.location else None,
            signal.location.address_text if signal.location else None,
            signal.reporter_id,
            signal.status.get_state_display() if signal.status else None,
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
        'stadsdeel',
        'address',
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
    """
    Write ZIP file of "horeca" data to storage.

    Note:
    - Django storage is configured to write files locally or to "object store".
    """
    category = _get_horeca_main_category()
    csv_files = []  # TODO: consider removing these

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Dump data in sub directory of the current temp directory, so that we
        # can use the current directory to eventually write the zip archive.
        base_name = f'sia-horeca-{isoyear}-week-{isoweek}'
        dump_dir = os.path.join(tmp_dir, base_name)
        os.makedirs(dump_dir)

        for sub_category in category.children.all():
            csv_file = create_csv_per_sub_category(
                sub_category, dump_dir, isoweek=isoweek, isoyear=isoyear
            )
            csv_files.append(csv_file)

        # Create zip file in current temp directory.
        target_zip = os.path.join(tmp_dir, base_name)
        actual_zip = shutil.make_archive(target_zip, format='zip', root_dir=dump_dir)
        epoch = time.time()
        target_zip_filename = os.path.basename(actual_zip)[:-4] + f'-{epoch}.zip'

        with open(actual_zip, 'rb') as opened_zip:
            export_obj = HorecaCSVExport(isoweek=isoweek, isoyear=isoyear)
            export_obj.uploaded_file.save(target_zip_filename, File(opened_zip), save=True)
            export_obj.save()

    return csv_files
