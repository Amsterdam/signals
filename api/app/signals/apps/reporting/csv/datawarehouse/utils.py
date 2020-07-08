"""
Dump CSV of SIA tables matching the old, agreed-upon, format.
"""
import csv
import logging
import os
import shutil
from typing import TextIO

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import connection
from django.db.models import Case, CharField, QuerySet, Value, When
from django.utils import timezone

from signals.apps.reporting.csv.utils import _get_storage_backend

logger = logging.getLogger(__name__)


def get_swift_parameters() -> dict:
    """
    Get Swift parameters

    :return dict:
    """
    return {
        'api_auth_url': settings.DWH_SWIFT_AUTH_URL,
        'api_username': settings.DWH_SWIFT_USERNAME,
        'api_key': settings.DWH_SWIFT_PASSWORD,
        'tenant_name': settings.DWH_SWIFT_TENANT_NAME,
        'tenant_id': settings.DWH_SWIFT_TENANT_ID,
        'region_name': settings.DWH_SWIFT_REGION_NAME,
        'container_name': settings.DWH_SWIFT_CONTAINER_NAME,
        'auto_overwrite': True,
    }


def save_csv_files(csv_files: list) -> None:
    """
    Writes the CSV files to the storage backend for the Datawarehouse

    :param csv_files:
    :returns None:
    """
    storage = _get_storage_backend(get_swift_parameters())

    for csv_file_path in csv_files:
        with open(csv_file_path, 'rb') as opened_csv_file:
            file_name = os.path.basename(opened_csv_file.name)
            storage.save(name=file_name, content=opened_csv_file)

            if isinstance(storage, FileSystemStorage):
                # Saves the file in a folder structure like "Y/m/d/file_name" for local storage
                now = timezone.now()
                file_path = f'{now:%Y}/{now:%m}/{now:%d}/{now:%H%M%S%Z}_{file_name}'
                storage.save(name=file_path, content=opened_csv_file)


def queryset_to_csv_file(queryset: QuerySet, csv_file_path: str) -> TextIO:
    """
    Creates the CSV file based on the given queryset and stores it in the given csv file path

    :param queryset:
    :param csv_file_path:
    :return TextIO:
    """
    sql, params = queryset.query.sql_with_params()
    sql = f"COPY ({sql}) TO STDOUT WITH (FORMAT CSV, HEADER, DELIMITER E',')"
    sql = sql.replace('AS "_', 'AS "')

    with open(csv_file_path, 'w') as file:
        with connection.cursor() as cursor:
            sql = cursor.mogrify(sql, params)
            cursor.copy_expert(sql, file)
    return file


def map_choices(field_name: str, choices: list) -> Case:
    """
    Creates a mapping for Postgres with case and when statements

    :param field_name:
    :param choices:
    :return Case:
    """
    return Case(
        *[When(**{field_name: value, 'then': Value(str(representation))})
          for value, representation in choices],
        output_field=CharField()
    )


def reorder_csv(file_path, ordered_field_names):
    reordered_file_path = f'{file_path[-4]}_reordered.csv'
    with open(file_path, 'r') as infile, open(reordered_file_path, 'a') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=ordered_field_names)
        writer.writeheader()
        for row in csv.DictReader(infile):
            writer.writerow(row)

    shutil.move(reordered_file_path, file_path)
