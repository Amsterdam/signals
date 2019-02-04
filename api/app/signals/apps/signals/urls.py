from django.urls import include, path

from signals.apps.signals.v0 import views as v0_views
from signals.apps.signals.v0.routers import SignalsRouterVersion0
from signals.apps.signals.v1 import views as v1_views
from signals.apps.signals.v1.routers import SignalsRouterVersion1

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

# API Version 1
signal_router_v1 = SignalsRouterVersion1()
signal_router_v1.register(r'public/terms/categories',
                          v1_views.MainCategoryViewSet,
                          base_name='category')
signal_router_v1.register(r'private/signals',
                          v1_views.PrivateSignalViewSet,
                          base_name='private-signals')
signal_router_v1.register(r'public/signals',
                          v1_views.PublicSignalViewSet,
                          base_name='public-signals')


# Appending extra url route for sub category detail endpoint.
signal_router_v1.urls.append(
    path('public/terms/categories/<str:slug>/sub_categories/<str:sub_slug>',
         v1_views.SubCategoryViewSet.as_view({'get': 'retrieve'}),
         name='sub-category-detail'),
)

signal_router_v1.urls.append(
    path('pdf/SIA-<int:signal_id>.pdf',
         v1_views.GeneratePdfView.as_view(),
         name='signal-pdf-download'),
)

urlpatterns = [
    # API Version 0
    path('', include((signal_router_v0.urls, 'signals'), namespace='v0')),

    # API Version 1
    path('v1/', include((signal_router_v1.urls, 'signals'), namespace='v1')),
]
