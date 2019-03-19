from django.urls import include, path

from signals.apps.api.generics.views import SwaggerView
from signals.apps.api.v0 import views as v0_views
from signals.apps.api.v0.routers import SignalsRouterVersion0

# API Version 0
signal_router_v0 = SignalsRouterVersion0()
signal_router_v0.register(r'signal/image', v0_views.SignalImageUpdateView, basename='signal-img')
signal_router_v0.register(r'signal', v0_views.SignalViewSet, basename='signal')
signal_router_v0.register(r'auth/signal', v0_views.SignalAuthViewSet, basename='signal-auth')
signal_router_v0.register(r'auth/status', v0_views.StatusAuthViewSet, basename='status-auth')
signal_router_v0.register(r'auth/category', v0_views.CategoryAuthViewSet, basename='category-auth')
signal_router_v0.register(r'auth/location', v0_views.LocationAuthViewSet, basename='location-auth')
signal_router_v0.register(r'auth/priority', v0_views.PriorityAuthViewSet, basename='priority-auth')
signal_router_v0.register(r'auth/note', v0_views.NoteAuthViewSet, basename='note-auth')

urlpatterns = [
    # AP Version 0
    path('', include((signal_router_v0.urls, 'signals'), namespace='v0')),

    # API Version 1
    path('', include(('signals.apps.api.v1.urls', 'signals'), namespace='v1')),

    # Swagger
    path('swagger/openapi.yaml', SwaggerView.as_view()),
]
