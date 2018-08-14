"""
SIA URL Configuration
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from signals.apps.signals import views as api_views

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),
    path('signals/', include('signals.apps.signals.urls')),
    path('signals/auth/me/', api_views.LocationUserView.as_view()),
    path('signals/admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
