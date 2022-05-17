# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.contrib.gis.db import models

logger = logging.getLogger(__name__)


class FeedbackManager(models.Manager):
    def request_feedback(self, signal):
        return self.create(**{'_signal': signal})
