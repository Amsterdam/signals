import os
from typing import Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from swift.storage import SwiftStorage

_default = os.getenv('SWIFT_DEFAULT_USING', 'default')


def _get_storage_backend(using: str = _default) -> Union[FileSystemStorage, SwiftStorage]:
    """
    Returns a SwiftStorage class OR a FileSystemStorage

    When not providing a "using" value the "default" settings will be used, this means that the normal SWIFT_* settings
    must be set properly. Otherwise the code will look for the settings in the SWIFT dict where "using" must be a
    existing key containing a dict of settings.

    To disable Swift storage the SWIFT_ENABLED environment variable can be set to anything but
    True, 1, '1', 'True', 'true'. When the Swift storage is disabled a FileSystemStorage will be returned.

    :param using:
    :returns: FileSystemStorage or SwiftStorage instance
    """
    if os.getenv('SWIFT_ENABLED', False) not in [True, 1, '1', 'True', 'true']:
        return FileSystemStorage(location=settings.DWH_MEDIA_ROOT)

    if not hasattr(settings, 'SWIFT'):
        raise ImproperlyConfigured('SWIFT settings must be set!')

    swift_settings = settings.SWIFT.get(using, {}) if using != _default else {}
    return SwiftStorage(**swift_settings)
