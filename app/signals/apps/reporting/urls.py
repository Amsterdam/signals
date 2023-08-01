# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from django.urls import re_path

from signals.apps.reporting.rest_framework.views import (
    PrivateReportSignalsOpenPerCategoryView,
    PrivateReportSignalsReopenRequestedPerCategory
)

urlpatterns = [
    re_path(r'private/reports/signals/open/?',
            PrivateReportSignalsOpenPerCategoryView.as_view({'get': 'list'}),
            name='reporting-signals-open-per-category-view'),
    re_path(r'private/reports/signals/reopen-requested/?',
            PrivateReportSignalsReopenRequestedPerCategory.as_view({'get': 'list'}),
            name='reporting-signals-reopen-requested-per-category-view'),
]
