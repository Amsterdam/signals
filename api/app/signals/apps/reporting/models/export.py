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


class SignalsCSVWriter():
    """Write current state of Signals in a Signals queryset to a CSV file."""
    def _get_extra_column_names(self, signals_qs):
        """Iterate over Signals queryset, derive set of extra_proprties column names."""
        column_names = set()
        for extra_properties in signals_qs.only('extra_properties').iterator(chunk_size=2000):
            if not extra_properties:
                continue

            for prop in extra_properties:
                if isinstance(prop, str):
                    continue  # old style, we ignore these
                column_names.add(prop['id'])

        return column_names

    def _get_empty_row(self, signals_qs):
        # Basic column names that derive from Signals model
        empty = OrderedDict((cn, None) for cn in self.column_names)

        # Extra column names that derive from extra properties
        extra_column_names = list(self._get_extra_column_names(signals_qs))
        extra_column_names.sort()
        empty.update(OrderedDict((cn, None) for cn in extra_column_names))

        return empty

    def writerows(self, signals_qs):
        empty = self._get_empty_row(signals_qs)

        for signal in signals_qs.iterator(chunk_size=2000):
            extra = copy.copy(empty)
            row = {
                'id': signal.pk,
                'signal_uuid': signal.signal_id,
                # more here
            }

            if not extra_properties:



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
        interval, categories, _ = get_parameters(export_parameters)
        categories = categories.select_related('parent')

        # TODO: refactor get_parameters to use get_full_interval_info directly
        interval = get_full_interval_info(export_parameters)

        # derive zip file name
        zip_basename = f'{basename}-{interval.desc}'

        with tempfile.TemporaryDirectory() as tmp_dir:
            for cat in categories:
                if cat.parent is None:
                    pass  # No signals associated only with main categories

                matching_signals = (
                    Signal.objects
                    .select_related('category_assignment__category')
                    .filter(category_assignment__catgory=cat)
                    .filter(created_at__gte=interval.t_begin)
                    .filter(created_at__lt=interval.t_end)
                )
                # create a per category CSV in temporary directory
                filename = f'signals-{cat.slug}-{cat.parent.slug}-{interval.desc}.csv'
                dump_dir = os.path.join(tmp_dir, zip_basename)
                # -->> SignalsCSVWriter -->>
                self._dump_signals_csv(matching_signals, dump_dir, filename)  # TBD, implement
            # Zip up all the single-category CSV files.
            target_zip = os.path.join(tmp_dir, zip_basename)
            actual_zip = shutil.make_archive(target_zip, format='zip', root_dir=dump_dir)

            # upload the ZIP
            target_zip_filename = os.path.basename(actual_zip)

            with open(actual_zip, 'rb') as opened_zip:
                csv_export = CSVExport(export_parameters=export_parameters)
                csv_export.uploaded_file.save(target_zip_filename, File(opened_zip, save=True))
                csv_export.save()

        return csv_export


class CSVExport(ExportParametersMixin):
    """CSV export parametrized on interval and categories."""
    created_by = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    uploaded_file = models.FileField(upload_to='category_exports/%Y', storage=storage, null=True)

    objects = CSVExportManager()
