from collections import OrderedDict
import copy
import csv
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.gis.db import models
from django.core.files import File

from signals.apps.reporting.csv.utils import _get_storage_backend
from signals.apps.reporting.models.mixin import (
    ExportParametersMixin,
    get_full_interval_info,
    get_parameters
)
from signals.apps.signals.models import Signal

# TODO: consider moving this to a central location (settings?)


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
        'temp_url_key': settings.HORECA_SWIFT_TEMP_URL_KEY,
        'temp_url_duration': settings.HORECA_SWIFT_TEMP_URL_DURATION,
        'use_temp_urls': settings.HORECA_SWIFT_USE_TEMP_URLS,
        'auto_overwrite': settings.HORECA_SWIFT_AUTO_OVERWRITE,
    }


storage = _get_storage_backend(get_swift_parameters())


class HorecaCSVExport(models.Model):
    class Meta:
        ordering = ('-isoyear', '-isoweek', '-created_at')

    created_by = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    isoweek = models.IntegerField()
    isoyear = models.IntegerField()
    uploaded_file = models.FileField(upload_to='exports/%Y', storage=storage)


class SignalCSVWriter:
    """Write current state of Signals in a Signals queryset to a CSV file."""
    STANDARD_COLUMN_NAMES = [
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
    ]

    def __init__(self, opened_file, signals_qs):
        self.opened_file = opened_file
        self.signals_qs = signals_qs

    def get_extra_column_names(self):
        # Make one pass over the queryset, determine extra_properties column names
        accumulator = set()
#        for extra_properties in self.signals_qs.only('extra_properties').iterator(chunk_size=2000):
        for signal in self.signals_qs.iterator(chunk_size=2000):
            if not signal.extra_properties:
                continue

            for prop in signal.extra_properties:
                if isinstance(prop, str):
                    continue  # old style, we ignore these
                accumulator.add(prop['id'])

        # Return sorted list of extra properties column names.
        column_names = list(accumulator)
        column_names.sort()

        return column_names

    def iterate_queryset(self):
        for signal in self.signals_qs.iterator(chunk_size=2000):
            row = {
                'id': signal.pk,
                'signal_uuid': signal.signal_id,
                'source': signal.source,
                'text': signal.text,
                'text_extra': signal.text_extra,
                'incident_date_start': signal.incident_date_start,
                'incident_date_end': signal.incident_date_end,
                'created_at': signal.created_at,
                'updated_at': signal.updated_at,
                'operational_date': signal.operational_date,
                'expire_date': signal.expire_date,
                'upload': signal.upload,
                'category_assignment_id': signal.category_assignment_id,
                'stadsdeel': signal.location.stadsdeel if signal.location else None,
                'address': signal.location.address_text if signal.location else None,
                'reporter_id': signal.reporter_id,
                'status_id': signal.status.get_state_display() if signal.status else None,
            }

            if signal.extra_properties:
                for extra_property in signal.extra_properties:
                    if isinstance(extra_property, str):
                        continue  # old style, we ignore these

                    answer = None
                    if isinstance(extra_property['answer'], str):
                        answer = extra_property['answer']
                    elif 'value' in extra_property['answer']:
                        answer = extra_property['answer']['value']
                    elif 'label' in extra_property['answer']:
                        answer = extra_property['answer']['label']

                    row[extra_property['id']] = answer
            yield row

    def writerows(self):
        column_names = copy.deepcopy(__class__.STANDARD_COLUMN_NAMES)
        column_names.extend(self.get_extra_column_names())

        dw = csv.DictWriter(self.opened_file, column_names, restval='', extrasaction='ignore')
        dw.writerows(self.iterate_queryset())


class CSVExportManager(models.Manager):
    def _dump_signals_csv(self, signals_qs, dump_dir, filename):
        """
        Write CSV for selected signal instances, only dump current state.
        """
        rows = self._create_rows(signals_qs)
        with open(os.path.join(), 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(rows)

    def create_csv_export(self, basename, export_parameters):
        # TODO: implement support for areas
        t_begin, t_end, categories, _ = get_parameters(export_parameters)
        categories = categories.select_related('parent')

        # TODO: refactor get_parameters to use get_full_interval_info directly
        interval = get_full_interval_info(export_parameters)

        # derive zip file name
        zip_basename = f'{basename}-{interval.desc}'

        with tempfile.TemporaryDirectory() as tmp_dir:
            dump_dir = os.path.join(tmp_dir, zip_basename)
            os.makedirs(dump_dir)

            for cat in categories:
                if cat.parent is None:
                    pass  # No signals associated only with main categories

                matching_signals = (
                    Signal.objects
                    .select_related('category_assignment__category')
                    .filter(category_assignment__category=cat)
                    .filter(created_at__gte=interval.t_begin)
                    .filter(created_at__lt=interval.t_end)
                )
                # create a per category CSV in temporary directory
                filename = f'signals-{cat.slug}-{cat.parent.slug}-{interval.desc}.csv'

                with open(os.path.join(dump_dir, filename), 'w') as f:
                    writer = SignalCSVWriter(f, matching_signals)
                    writer.writerows()

            # Zip up all the single-category CSV files.
            target_zip = os.path.join(tmp_dir, zip_basename)
            actual_zip = shutil.make_archive(target_zip, format='zip', root_dir=dump_dir)

            # upload the ZIP
            target_zip_filename = os.path.basename(actual_zip)

            with open(actual_zip, 'rb') as opened_zip:
                csv_export = CSVExport(export_parameters=export_parameters)
                csv_export.uploaded_file.save(target_zip_filename, File(opened_zip), save=True)
                csv_export.save()

        return csv_export


class CSVExport(ExportParametersMixin):
    """CSV export parametrized on interval and categories."""
    created_by = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    uploaded_file = models.FileField(upload_to='category_exports/%Y', storage=storage, null=True)

    objects = CSVExportManager()
