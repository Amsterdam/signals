"""
SIA URL Configuration
"""
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from rest_framework import permissions

from signals import views as api_views


class SignalsView(routers.APIRootView):
    """
    List Signals and their related information.

    These API endpoints are part of the Signalen Informatievoorziening Amsterdam
    (SIA) application. SIA can be used by citizens and interested parties to inform
    the Amsterdam municipality of problems in public spaces (like noise complaints,
    broken street lights etc.) These signals (signalen in Dutch) are then followed
    up on by the appropriate municipal services.

    The code for this application (and associated web front-end) is available from:
    - https://github.com/Amsterdam/signals
    - https://github.com/Amsterdam/signals-frontend

    Note:
    Most of these endpoints require authentication. The only fully public endpoint
    is /signals/signal where new signals can be POSTed.
    """


class SignalRouter(routers.DefaultRouter):
    APIRootView = SignalsView


signals = SignalRouter()

signals.register(
    r"signal/image", api_views.SignalImageUpdateView, base_name="img")
signals.register(
    r"signal", api_views.SignalView, base_name="signal")
signals.register(
    r"auth/signal", api_views.SignalAuthView, base_name="signal-auth")

# signals.register(
#     r"status", api_views.StatusView, base_name="status")
signals.register(
    r"auth/status", api_views.StatusAuthView, base_name="status-auth")

# signals.register(
#     r"category", api_views.CategoryView, base_name="category")
signals.register(
    r"auth/category", api_views.CategoryAuthView, base_name="category-auth")

# signals.register(
#     r"location", api_views.LocationView, base_name="location")
signals.register(
    r"auth/location", api_views.LocationAuthView, base_name="location-auth")

# signals.register(
#     r"auth/me", api_views.LocationUserView, base_name="me-auth")


urls = signals.urls

schema_view = get_schema_view(
   openapi.Info(
      title="Signals API",
      default_version='v1',
      description="Signals in Amsterdam",
      terms_of_service="https://data.amsterdam.nl/",
      contact=openapi.Contact(email="datapunt@amsterdam.nl"),
      license=openapi.License(name="CC0 1.0 Universal"),
   ),
   validators=['flex', 'ssv'],
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^signals/swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=None), name='schema-json'),
    url(r'^signals/swagger/$',
        schema_view.with_ui(
            'swagger', cache_timeout=None),
        name='schema-swagger-ui'),
    url(r'^signals/redoc/$',
        schema_view.with_ui('redoc', cache_timeout=None), name='schema-redoc'),
    url(r"^signals/", include(urls)),
    url(r"^status/", include("signals.apps.health.urls")),
    path("signals/auth/me/", api_views.LocationUserView.as_view()),
    # TODO : where should the Django Admin endpoint be eventually
    path("signals/admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
