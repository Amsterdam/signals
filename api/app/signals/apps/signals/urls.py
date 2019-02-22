from django.urls import include, path

from signals.apps.signals.api_generics.views import SwaggerView
from signals.apps.signals.v0 import views as v0_views
from signals.apps.signals.v0.routers import SignalsRouterVersion0

# API Version 0
signal_router_v0 = SignalsRouterVersion0()
signal_router_v0.register(r'signal/image', v0_views.SignalImageUpdateView, base_name='signal-img')
signal_router_v0.register(r'signal', v0_views.SignalViewSet, base_name='signal')
signal_router_v0.register(r'auth/signal', v0_views.SignalAuthViewSet, base_name='signal-auth')
signal_router_v0.register(r'auth/status', v0_views.StatusAuthViewSet, base_name='status-auth')
signal_router_v0.register(r'auth/category', v0_views.CategoryAuthViewSet, base_name='category-auth')
signal_router_v0.register(r'auth/location', v0_views.LocationAuthViewSet, base_name='location-auth')
signal_router_v0.register(r'auth/priority', v0_views.PriorityAuthViewSet, base_name='priority-auth')
signal_router_v0.register(r'auth/note', v0_views.NoteAuthViewSet, base_name='note-auth')

urlpatterns = [
    # AP Version 0
    path('', include((signal_router_v0.urls, 'signals'), namespace='v0')),

    # API Version 1
    path('', include(('signals.apps.signals.v1.urls', 'signals'), namespace='v1')),

    # Swagger
    path('swagger/openapi.yaml', SwaggerView.as_view()),
]
