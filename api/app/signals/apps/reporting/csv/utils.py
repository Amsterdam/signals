import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from swift.storage import SwiftStorage


def _get_storage_backend(swift_parameters):
    """Return the storage backend (Object Store) specific for Horeca data delivery.

    :returns: FileSystemStorage or SwiftStorage instance
    """
    # TODO: Refactor this logic, belongs in app_settings and project settings

    if os.getenv('SWIFT_ENABLED', 'false') == 'true':
        return SwiftStorage(**swift_parameters)
    else:
        return FileSystemStorage(location=settings.DWH_MEDIA_ROOT)
