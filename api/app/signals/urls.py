# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from signals.apps.api.generics.routers import BaseSignalsAPIRootView

urlpatterns = [
    # Used to determine API health when deploying
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', BaseSignalsAPIRootView.as_view()),
    path('signals/', include('signals.apps.api.urls')),

    # Experimental API
    path('signals/', include('signals.apps.xperimental.rest_framework.urls')),

    # The Django admin
    path('signals/admin/', admin.site.urls),
    url(r'^signals/markdownx/', include('markdownx.urls')),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    media_root = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + media_root
