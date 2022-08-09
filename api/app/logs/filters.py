# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from logging import LogRecord, Filter

from django.conf import settings


class DebugQueryFilter(Filter):
    """
    Makes the query debug information dependant on the settings.
    """
    def filter(self, record: LogRecord) -> bool:
        return settings.LOG_QUERIES and settings.DEBUG


class StaticFieldFilter(Filter):
    """
    Python logging filter that adds the given static contextual information
    in the ``fields`` dictionary to all logging records.
    """

    def __init__(self, fields):
        self.static_fields = fields

    def filter(self, record):
        for k, v in self.static_fields.items():
            setattr(record, k, v)
        return True


class AzureEnabled(Filter):
    """
    Check for the Azure enabled flag to enable the azure logging
    """

    def filter(self, record: LogRecord):
        return False
