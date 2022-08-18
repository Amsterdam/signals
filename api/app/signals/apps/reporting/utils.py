# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2022 Gemeente Amsterdam
from typing import Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from storages.backends.azure_storage import AzureStorage
from swift.storage import SwiftStorage


def _get_storage_backend(using: str) -> Union[FileSystemStorage, AzureStorage, SwiftStorage]:
    """
    Returns a AzureStorage class OR a FileSystemStorage

    When providing a "using" value the code will look for the settings in the Azure dict where "using" must be a
    existing key containing a dict of settings.

    To disable Azure storage the AZURE_ENABLED environment variable can be set to anything but
    True, 1, '1', 'True', 'true'. When the Azure storage is disabled a FileSystemStorage will be returned.

    :param using:
    :returns: FileSystemStorage or AzureStorage instance
    """
    if settings.AZURE_ENABLED:
        if not hasattr(settings, 'AZURE_CONTAINERS'):
            raise ImproperlyConfigured('AZURE_CONTAINERS settings must be set!')
        return AzureStorage(**settings.AZURE_CONTAINERS.get(using, {}))

    if settings.SWIFT_ENABLED:  # TODO:: SIG-4733 azure-afterwork-delete
        if not hasattr(settings, 'SWIFT'):
            raise ImproperlyConfigured('SWIFT settings must be set!')
        return SwiftStorage(**settings.SWIFT.get(using, {}))

    return FileSystemStorage(location=settings.DWH_MEDIA_ROOT)
