"""Parkeervakken URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework import routers
from rest_framework import permissions

from . import views as api_views
from django.conf import settings


class SignalsView(routers.APIRootView):
    """
    List Signals and their related information

    Manage the incoming signals in Amsterdam

    !! IN TEST FASE !!
    """


class SignalRouter(routers.DefaultRouter):
    APIRootView = SignalsView


signals = SignalRouter()
signals.register(
    r"signal", api_views.SignalView, base_name="signal")
signals.register(
    r"auth/signal", api_views.SignalAuthView, base_name="signal-auth")

signals.register(
    r"status", api_views.StatusView, base_name="status")
signals.register(
    r"auth/status", api_views.StatusAuthView, base_name="status-auth")

signals.register(
    r"category", api_views.CategoryView, base_name="category")
signals.register(
    r"auth/category", api_views.CategoryView, base_name="category-auth")

signals.register(
    r"location", api_views.LocationView, base_name="location")
signals.register(
    r"auth/location", api_views.LocationAuthView, base_name="location-auth")


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
    url(r"^status/", include("signals.health.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
