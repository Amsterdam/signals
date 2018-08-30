from django.urls import path, include
from rest_framework import routers

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

urlpatterns = [
    path('', include(signal_router.urls)),
]
