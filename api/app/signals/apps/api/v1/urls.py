from urllib.parse import urlparse

from django.urls import include, path, resolve

from signals.apps.api.v1.private import views as v1_private_views
from signals.apps.api.v1.private.views import SignalCategoryRemovedAfterViewSet
from signals.apps.api.v1.public import views as v1_public_views
from signals.apps.api.v1.routers import SignalsRouterVersion1
from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.signals.models import Category

# API Version 1
signal_router_v1 = SignalsRouterVersion1()

signal_router_v1.register(
    r'public/terms/categories',
    v1_public_views.ParentCategoryViewSet,
    basename='category'
)

signal_router_v1.register(
    r'private/signals',
    v1_private_views.PrivateSignalViewSet,
    basename='private-signals'
)

signal_router_v1.register(
    r'public/signals',
    v1_public_views.PublicSignalViewSet,
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
    r'private/status-message-templates',
    v1_private_views.StoreStatusMessageTemplates,
    basename='private-status-message-templates'
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
        v1_public_views.ChildCategoryViewSet.as_view({'get': 'retrieve'}),
        name='category-detail'
    )
)

# Appending extra routes for status message templates
signal_router_v1.urls.append(
    path(
        'public/terms/categories/<str:slug>/status-message-templates',
        v1_public_views.ChildCategoryViewSet.as_view({'get': 'status_message_templates'}),
        name='status_message_templates_main_category'
    )
)
signal_router_v1.urls.append(
    path(
        'public/terms/categories/<str:slug>/sub_categories/<str:sub_slug>/status-message-templates',
        v1_public_views.ChildCategoryViewSet.as_view({'get': 'status_message_templates'}),
        name='status_message_templates'
    )
)

# Status message templates are only editable via the private API
signal_router_v1.urls.append(
    path(
        'private/status-message-templates',
        v1_private_views.StoreStatusMessageTemplates,
        name='private-status-message-templates'
    )
)


# PDF

# New PDF route according to the correct URL convention
signal_router_v1.urls.append(
    path(
        'private/signals/<int:pk>/pdf',
        v1_private_views.GeneratePdfView.as_view(),
        name='signal-pdf-download'
    )
)

signal_router_v1.urls.append(
    path(
        'relations',
        v1_public_views.NamespaceView.as_view(),
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
