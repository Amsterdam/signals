from django.urls import include, path
from rest_framework import routers

from signals.apps.signals import views


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


# API Version 0
signal_router_v0 = SignalRouter()
signal_router_v0.register(r'signal/image', views.SignalImageUpdateView, base_name='signal-img')
signal_router_v0.register(r'signal', views.SignalViewSet, base_name='signal')
signal_router_v0.register(r'auth/signal', views.SignalAuthViewSet, base_name='signal-auth')
signal_router_v0.register(r'auth/status', views.StatusAuthViewSet, base_name='status-auth')
signal_router_v0.register(r'auth/category', views.CategoryAuthViewSet, base_name='category-auth')
signal_router_v0.register(r'auth/location', views.LocationAuthViewSet, base_name='location-auth')
signal_router_v0.register(r'auth/priority', views.PriorityAuthViewSet, base_name='priority-auth')

# API Version 1
signal_router_v1 = SignalRouter(trailing_slash=False)
signal_router_v1.register(r'public/terms/categories',
                          views.MainCategoryViewSet,
                          base_name='category')

urlpatterns = [
    # API Version 0
    path('', include(signal_router_v0.urls)),

    # API Version 1
    path('v1/', include(signal_router_v1.urls)),
    path('v1/public/terms/categories/<str:slug>/subcategories/<str:sub_slug>',
         views.SubCategoryViewSet.as_view({'get': 'retrieve'}),
         name='sub-category-detail'),
]
