import csv
import logging
import os
import shutil
import zipfile
from typing import TextIO

from django.db import connection
from django.db.models import Case, CharField, QuerySet, Value, When
from django.utils import timezone
from swift.storage import SwiftStorage

from signals.apps.reporting.utils import _get_storage_backend

logger = logging.getLogger(__name__)


def zip_csv_files(files_to_zip: list, using: str) -> None:
    """
    Writes zip file of the generated csv files in the {now:%Y}/{now:%m}/{now:%d} folder

    :returns:
    """
    storage = _get_storage_backend(using=using)
    now = timezone.now()
    src_folder = f'{storage.location}/{now:%Y}/{now:%m}/{now:%d}'
    dst_file = os.path.join(src_folder, f'{now:%Y%m%d_%H%M%S%Z}')

    with zipfile.ZipFile(f'{dst_file}.zip', 'w') as zipper:
        for file in files_to_zip:
            if file:
                base_file = os.path.basename(file)
                zipper.write(
                    filename=os.path.join(src_folder, base_file),
                    arcname=base_file,
                    compress_type=zipfile.ZIP_DEFLATED
                )


def save_csv_files(csv_files: list, using: str, path: str = None) -> None:
    """
    Writes the CSV files to the configured storage backend
    This could either be the SwiftStorage or a local FileSystemStorage

    :param csv_files:
    :param using:
    :returns None:
    """
    storage = _get_storage_backend(using=using)
    stored_csv = list()
    for csv_file_path in csv_files:
        with open(csv_file_path, 'rb') as opened_csv_file:
            file_name = os.path.basename(opened_csv_file.name)
            file_path = None
            if isinstance(storage, SwiftStorage):
                file_path = f'{path}{file_name}' if path else file_name
                storage.save(name=file_path, content=opened_csv_file)
            else:
                # Saves the file in a folder structure like "Y/m/d/file_name" for local storage
                now = timezone.now()
                file_path = f'{now:%Y}/{now:%m}/{now:%d}/{now:%H%M%S%Z}_{file_name}'
                storage.save(name=file_path, content=opened_csv_file)
            stored_csv.append(os.path.basename(file_path))
    return stored_csv


def queryset_to_csv_file(queryset: QuerySet, csv_file_path: str) -> TextIO:
    """
    Creates the CSV file based on the given queryset and stores it in the given csv file path

    Special thanks for Mehdi Pourfar and his post about "Faster CSV export with Django & Postgres"
    https://dev.to/mehdipourfar/faster-csv-export-with-django-postgres-5bi5

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
    reordered_file_path = f'{file_path[:-4]}_reordered.csv'
    with open(file_path, 'r') as infile, open(reordered_file_path, 'a') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=ordered_field_names)
        writer.writeheader()
        for row in csv.DictReader(infile):
            writer.writerow(row)

    shutil.move(file_path, f'{file_path[:-4]}_original.csv')
    shutil.move(reordered_file_path, file_path)
