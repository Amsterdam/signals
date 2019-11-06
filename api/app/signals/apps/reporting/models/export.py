from django.core.files import File
from django.conf import settings
from django.contrib.gis.db import models

from signals.apps.reporting.csv.utils import _get_storage_backend
from signals.apps.reporting.models.mixin import ExportParametersMixin, get_parameters
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


class CSVExportManager(models.Manager):
    def create_csv_export(self, basename, export_parameters):
        # TODO: implement support for areas
        t_begin, t_end, categories, _ = get_parameters(export_parameters)
        categories = categories.select_related('parent')

        # TODO: derive zip file name that is appropriate, based on basename and
        # the currently defined interval (daily, weekly, monthly)

        with tempfile.TemporaryDirectory() as tmp_dir:
            for cat in categories:
                if cat.parent is None:
                    pass  # No signals associated only with main categories

                matching_signals = (
                    Signal.objects
                    .select_related('category_assignment__category')
                    .filter(category_assignment__catgory=cat)
                    .filter(created_at__gte=t_begin)
                    .filter(created_at__lt=t_end)
                )
                # TODO: create CSV in this loop iteration
            # TODO: create a ZIP file of all the created CSV files

        csv_export = CSVExport(export_parameters=export_parameters)
        csv_export.uploaded_file.save(target_zip_filename, File(opened_zip, save=True)
        csv_export.save()

        return csv_export


class CSVExport(ExportParametersMixin):
    """CSV export parametrized on interval and categories."""
    created_by = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    uploaded_file = models.FileField(upload_to='category_exports/%Y', storage=storage, null=True)

    objects = CSVExportManager()
