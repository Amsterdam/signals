from django.urls import include, path

from signals.apps.signals import routers, views
from signals.apps.signals.v1.views import (
    GeneratePdfView,
    MainCategoryViewSet,
    PrivateSignalViewSet,
    SubCategoryViewSet,
)

# API Version 0
signal_router_v0 = routers.SignalsRouterVersion0()
signal_router_v0.register(r'signal/image', views.SignalImageUpdateView, base_name='signal-img')
signal_router_v0.register(r'signal', views.SignalViewSet, base_name='signal')
signal_router_v0.register(r'auth/signal', views.SignalAuthViewSet, base_name='signal-auth')
signal_router_v0.register(r'auth/status', views.StatusAuthViewSet, base_name='status-auth')
signal_router_v0.register(r'auth/category', views.CategoryAuthViewSet, base_name='category-auth')
signal_router_v0.register(r'auth/location', views.LocationAuthViewSet, base_name='location-auth')
signal_router_v0.register(r'auth/priority', views.PriorityAuthViewSet, base_name='priority-auth')
signal_router_v0.register(r'auth/note', views.NoteAuthViewSet, base_name='note-auth')

# API Version 1
signal_router_v1 = routers.SignalsRouterVersion1()
signal_router_v1.register(r'public/terms/categories',
                          MainCategoryViewSet,
                          base_name='category')
signal_router_v1.register(r'private/signals',
                          PrivateSignalViewSet,
                          base_name='private-signals')

# Appending extra url route for sub category detail endpoint.
signal_router_v1.urls.append(
    path('public/terms/categories/<str:slug>/sub_categories/<str:sub_slug>',
         SubCategoryViewSet.as_view({'get': 'retrieve'}),
         name='sub-category-detail'),
)

signal_router_v1.urls.append(
    path('pdf/SIA-<int:signal_id>.pdf',
         GeneratePdfView.as_view(),
         name='signal-pdf-download'),
)

urlpatterns = [
    # API Version 0
    path('', include((signal_router_v0.urls, 'signals'), namespace='v0')),

    # API Version 1
    path('v1/', include((signal_router_v1.urls, 'signals'), namespace='v1')),
]
