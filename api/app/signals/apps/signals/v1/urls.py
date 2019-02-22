from django.urls import include, path

from signals.apps.signals.v1.private import views as v1_private_views
from signals.apps.signals.v1.public import views as v1_public_views
from signals.apps.signals.v1.routers import SignalsRouterVersion1

# API Version 1
signal_router_v1 = SignalsRouterVersion1()

signal_router_v1.register(
    r'public/terms/categories',
    v1_public_views.MainCategoryViewSet,
    base_name='category'
)

signal_router_v1.register(
    r'private/signals',
    v1_private_views.PrivateSignalViewSet,
    base_name='private-signals'
)

signal_router_v1.register(
    r'public/signals',
    v1_public_views.PublicSignalViewSet,
    base_name='public-signals'
)

# Private split
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/split',
        v1_private_views.PrivateSignalSplitViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
        name='private-signals-split'
    )
)

# Private attachments
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/attachments',
        v1_private_views.PrivateSignalAttachmentsViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='private-signals-attachments'
    )
)

# Public attachments
signal_router_v1.urls.append(
    path(
        'public/signals/<str:signal_id>/attachments',
        v1_public_views.PublicSignalAttachmentsViewSet.as_view({'post': 'create'}),
        name='public-signals-attachments'
    )
)

# Appending extra url route for sub category detail endpoint.
signal_router_v1.urls.append(
    path(
        'public/terms/categories/<str:slug>/sub_categories/<str:sub_slug>',
        v1_public_views.SubCategoryViewSet.as_view({'get': 'retrieve'}),
        name='sub-category-detail'
    )
)

# PDF
signal_router_v1.urls.append(
    path(
        'pdf/SIA-<int:signal_id>.pdf',
        v1_private_views.GeneratePdfView.as_view(),
        name='signal-pdf-download'
    )
)

urlpatterns = [
    path('v1/', include(signal_router_v1.urls)),
]
