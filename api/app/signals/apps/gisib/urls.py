# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.gisib.rest_framework.views.quercus import PublicGISIBFeatureCollectionViewSet

router = SignalsRouter()

router.register('public/gisib', PublicGISIBFeatureCollectionViewSet, basename='collections')

urlpatterns = [
    path('', include((router.urls, 'signals.apps.gisib'), namespace='gisib')),
]
