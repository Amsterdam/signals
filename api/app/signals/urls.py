"""
SIA URL Configuration
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),
    path('signals/', include('signals.apps.signals.urls')),
    path('signals/admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
