# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from django.conf import settings
from django.contrib import admin

from signals.apps.classification.admin.admins import ClassifierAdmin, TrainingSetAdmin
from signals.apps.classification.models import TrainingSet
from signals.apps.classification.models.classifier import Classifier

if settings.FEATURE_FLAGS.get("CLASSIFICATION_ENABLED"):
    admin.site.register(TrainingSet, TrainingSetAdmin)
    admin.site.register(Classifier, ClassifierAdmin)
