# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from typing import Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from storages.backends.azure_storage import AzureStorage


def _get_storage_backend(using: str) -> Union[AzureStorage, FileSystemStorage]:
    """
    Returns one of the following storages:
        - AzureStorage, the "using" must be present in the AZURE_CONTAINERS setting.
        - FileSystemStorage, location is set to the settings.DWH_MEDIA_ROOT.

    :param using:
    :returns: AzureStorage or FileSystemStorage
    """
    if settings.AZURE_STORAGE_ENABLED:
        if not hasattr(settings, 'AZURE_CONTAINERS'):
            raise ImproperlyConfigured('AZURE_CONTAINERS settings must be set!')
        if using not in settings.AZURE_CONTAINERS.keys():
            raise ImproperlyConfigured(f'{using} not present in the AZURE_CONTAINERS settings')

        return AzureStorage(**settings.AZURE_CONTAINERS.get(using, {}))
    else:
        return FileSystemStorage(location=settings.DWH_MEDIA_ROOT)
