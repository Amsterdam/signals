from django.conf.urls import include, url
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from signals.apps.signals import views as api_views


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


signal_router = SignalRouter()

signal_router.register(r'signal/image', api_views.SignalImageUpdateView, base_name='signal-img')
signal_router.register(r'signal', api_views.SignalViewSet, base_name='signal')
signal_router.register(r'auth/signal', api_views.SignalAuthViewSet, base_name='signal-auth')
signal_router.register(r'auth/status', api_views.StatusAuthViewSet, base_name='status-auth')
signal_router.register(r'auth/category', api_views.CategoryAuthViewSet, base_name='category-auth')
signal_router.register(r'auth/location', api_views.LocationAuthViewSet, base_name='location-auth')

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
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=None),
        name='schema-json'),
    url(r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=None),
        name='schema-swagger-ui'),
    url(r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=None),
        name='schema-redoc'),
    path('', include(signal_router.urls)),
]
