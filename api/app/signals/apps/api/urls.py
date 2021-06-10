# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import BaseSignalsRouter
from signals.apps.api.generics.views import SwaggerView
from signals.apps.api.views.ml_tool_proxy import LegacyMlPredictCategoryView

# Base router
base_signal_router = BaseSignalsRouter()

urlpatterns = [
    # Because we use NamespaceVersioning we still need to include this as the "v0" namespace
    path('', include((base_signal_router.urls, 'signals'), namespace='v0')),

    # Legacy prediction proxy endpoint, still needed
    path('category/prediction', LegacyMlPredictCategoryView.as_view(), name='ml-tool-predict-proxy'),

    # API Version 1
    path('', include(('signals.apps.api.urls_v1', 'signals'), namespace='v1')),

    # Swagger
    path('swagger/openapi.yaml', SwaggerView.as_view()),
]
