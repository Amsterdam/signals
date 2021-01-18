# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging
from urllib.parse import urlencode

from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel

logger = logging.getLogger(__name__)


class StoredSignalFilter(CreatedUpdatedModel):
    name = models.CharField(max_length=10000)
    created_by = models.EmailField(null=True, blank=True)
    options = models.JSONField(default=dict)
    refresh = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return '{}'.format(self.name)

    def url_safe_options(self):
        query_params = []
        for key, value in self.options.items():
            if not value:
                continue

            if isinstance(value, (list, tuple)):
                query_params += [urlencode({key: v}) for v in value]
            else:
                query_params.append(urlencode({key: value}))
        return '{}'.format('&'.join(query_params))
