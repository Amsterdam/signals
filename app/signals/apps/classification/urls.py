# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from django.urls import path

from signals.apps.classification.views import MlPredictCategoryView

urlpatterns = [
    path('category/prediction', MlPredictCategoryView.as_view(), name='ml-tool-predict-proxy'),
]
