# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from signals.apps.api.generics.routers import BaseSignalsAPIRootView

# Remove "view website" button in the Django admin
admin.site.site_url = None

urlpatterns = [
    # Used to determine API health when deploying
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', BaseSignalsAPIRootView.as_view()),
    path('signals/', include('signals.apps.api.urls')),

    # The media folder is routed with X-Sendfile when DEBUG=False and
    # with the Django static helper when DEBUG=True
    path('signals/media/', include('signals.apps.media.urls')),

    # The Django admin
    path('signals/admin/', admin.site.urls),
    re_path(r'^signals/markdownx/', include('markdownx.urls')),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),
]

if settings.OIDC_RP_CLIENT_ID:
    urlpatterns += [
        path('signals/oidc/login_failure/', TemplateView.as_view(template_name='admin/oidc/login_failure.html')),
        path('signals/oidc/', include('mozilla_django_oidc.urls')),
    ]

if settings.SILK_ENABLED:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

# DRF Spectacular
urlpatterns += [
    path('signals/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('signals/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
