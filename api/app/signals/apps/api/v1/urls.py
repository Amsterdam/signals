from urllib.parse import urlparse

from django.urls import include, path, resolve

from signals.apps.api.v1.routers import SignalsRouterVersion1
from signals.apps.api.v1.views import (
    ChildCategoryViewSet,
    GeneratePdfView,
    NamespaceView,
    ParentCategoryViewSet,
    PrivateSignalAttachmentsViewSet,
    PrivateSignalSplitViewSet,
    PrivateSignalViewSet,
    PublicSignalAttachmentsViewSet,
    PublicSignalViewSet,
    SignalCategoryRemovedAfterViewSet,
    StatusMessageTemplatesViewSet,
    StoredSignalFilterViewSet
)
from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.search.views import SearchView
from signals.apps.signals.models import Category

# API Version 1
signal_router_v1 = SignalsRouterVersion1()

signal_router_v1.register(
    r'public/terms/categories',
    ParentCategoryViewSet,
    basename='category'
)

signal_router_v1.register(
    r'private/signals',
    PrivateSignalViewSet,
    basename='private-signals'
)

signal_router_v1.register(
    r'public/signals',
    PublicSignalViewSet,
    basename='public-signals'
)

signal_router_v1.register(
    r'public/feedback/standard_answers',
    StandardAnswerViewSet,
    basename='feedback-standard-answers'
)

signal_router_v1.register(
    r'public/feedback/forms',
    FeedbackViewSet,
    basename='feedback-forms'
)

signal_router_v1.register(
    r'private/me/filters',
    StoredSignalFilterViewSet,
    basename='stored-signal-filters'
)

# Status message templates are only editable via the private API
signal_router_v1.urls.append(
    path(
        'private/terms/categories/<str:slug>/sub_categories/<str:sub_slug>/status-message-templates',  # noqa
        StatusMessageTemplatesViewSet.as_view({
            'get': 'retrieve', 'post': 'create'
         }),
        name='private-status-message-templates-child'
    )
)
signal_router_v1.urls.append(
    path(
        'private/terms/categories/<str:slug>/status-message-templates',
        StatusMessageTemplatesViewSet.as_view({
            'get': 'retrieve', 'post': 'create'
        }),
        name='private-status-message-templates-parent'
    )
)

# Private split
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/split',
        PrivateSignalSplitViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
        name='private-signals-split'
    )
)

# Private attachments
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/attachments',
        PrivateSignalAttachmentsViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='private-signals-attachments'
    )
)

# Public attachments
signal_router_v1.urls.append(
    path(
        'public/signals/<str:signal_id>/attachments',
        PublicSignalAttachmentsViewSet.as_view({'post': 'create'}),
        name='public-signals-attachments'
    )
)

# Appending extra url route for sub category detail endpoint.
signal_router_v1.urls.append(
    path(
        'public/terms/categories/<str:slug>/sub_categories/<str:sub_slug>',
        ChildCategoryViewSet.as_view({'get': 'retrieve'}),
        name='category-detail'
    )
)

# PDF

# New PDF route according to the correct URL convention
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/pdf',
        GeneratePdfView.as_view(),
        name='signal-pdf-download'
    )
)

signal_router_v1.urls.append(
    path(
        'relations',
        NamespaceView.as_view(),
        name='signal-namespace'
    )
)

signal_router_v1.urls.append(
    path(
        'private/signals/category/removed',
        SignalCategoryRemovedAfterViewSet.as_view({'get': 'list'}),
        name='signal-category-changed-since'
    )
)

# V1 disabled for now
#
# signal_router_v1.urls.append(
#     path(
#         'public/category/prediction',
#         v1_public_views.MLPredictCategoryView.as_view({'get': 'retrieve'}),
#         name='ml-predict-category'
#     )
# )

signal_router_v1.urls.append(
    path(
        'private/search',
        SearchView.as_view({'get': 'list'}),
        name='elastic-search'
    )
)

urlpatterns = [
    path('v1/', include(signal_router_v1.urls)),
]


def category_from_url(url: str):
    view, args, kwargs = resolve(
        (urlparse(url)).path
    )
    category = Category.objects.get(
        slug=kwargs['sub_slug'],
        parent__slug=kwargs['slug'],
    )
    return category
