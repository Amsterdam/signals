from django.urls import include, path

from signals.apps.api.v1.routers import SignalsRouterVersion1
from signals.apps.api.v1.views import (  # MLPredictCategoryView,  # V1 disabled for now
    ChildCategoryViewSet,
    GeneratePdfView,
    NamespaceView,
    ParentCategoryViewSet,
    PrivateAreasViewSet,
    PrivateCategoryViewSet,
    PrivateDepartmentViewSet,
    PrivateSignalAttachmentsViewSet,
    PrivateSignalSplitViewSet,
    PrivateSignalViewSet,
    PublicAreasViewSet,
    PublicQuestionViewSet,
    PublicSignalAttachmentsViewSet,
    PublicSignalViewSet,
    SignalCategoryRemovedAfterViewSet,
    StatusMessageTemplatesViewSet,
    StoredSignalFilterViewSet
)
from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.search.views import SearchView
from signals.apps.users.v1.views import PermissionViewSet, RoleViewSet, UserViewSet

# Public API
public_router = SignalsRouterVersion1()
public_router.register(r'public/terms/categories', ParentCategoryViewSet, basename='category')
public_router.register(r'public/signals', PublicSignalViewSet, basename='public-signals')
public_router.register(r'public/feedback/standard_answers', StandardAnswerViewSet, basename='feedback-standard-answers')
public_router.register(r'public/feedback/forms', FeedbackViewSet, basename='feedback-forms')
public_router.register(r'public/areas', PublicAreasViewSet, basename='public-areas')

# Private API
private_router = SignalsRouterVersion1()
private_router.register(r'private/signals', PrivateSignalViewSet, basename='private-signals')
private_router.register(r'private/me/filters', StoredSignalFilterViewSet, basename='stored-signal-filters')
private_router.register(r'private/users', UserViewSet, basename='user')
private_router.register(r'private/roles', RoleViewSet, basename='group')
private_router.register(r'private/permissions', PermissionViewSet, basename='permission')
private_router.register(r'private/departments', PrivateDepartmentViewSet, basename='department')
private_router.register(r'private/categories', PrivateCategoryViewSet, basename='private-category')
private_router.register(r'private/areas', PrivateAreasViewSet, basename='private-areas')

# Combined API
base_router = SignalsRouterVersion1()
base_router.registry.extend(public_router.registry)
base_router.registry.extend(private_router.registry)

urlpatterns = [
    # The base routes of the API
    path('v1/', include(base_router.urls)),

    # Used for namespacing SIA, a HAL standard
    path('v1/relations', NamespaceView.as_view(), name='signal-namespace'),

    # Public additions
    # path('v1/public/', include(public_router.urls)),
    path('v1/public/', include([
        path('signals/<str:signal_id>/attachments',
             PublicSignalAttachmentsViewSet.as_view({'post': 'create'}),
             name='public-signals-attachments'),
        path('terms/categories/<str:slug>/sub_categories/<str:sub_slug>',
             ChildCategoryViewSet.as_view({'get': 'retrieve'}),
             name='category-detail'),
        path('questions/',
             PublicQuestionViewSet.as_view({'get': 'list'}),
             name='question-detail'),
        # V1 disabled for now
        # path('category/prediction', MLPredictCategoryView.as_view({'get': 'retrieve'}), name='ml-predict-category'),
    ])),

    # Private additions
    path('v1/private/', include([
        # Returns the details of the currently logged in user
        path('me/', UserViewSet.as_view({'get': 'me'}), name='auth-me'),

        # Get/Replace the status message templates per category
        path('terms/categories/<str:slug>/status-message-templates',
             StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
             name='private-status-message-templates-parent'),
        path('terms/categories/<str:slug>/sub_categories/<str:sub_slug>/status-message-templates',
             StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
             name='private-status-message-templates-child'),

        # Additional Signals endpoints
        path('signals/<int:pk>/split',
             PrivateSignalSplitViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
             name='private-signals-split'),
        path('signals/<int:pk>/attachments',
             PrivateSignalAttachmentsViewSet.as_view({'get': 'list', 'post': 'create'}),
             name='private-signals-attachments'),
        path('signals/<int:pk>/pdf', GeneratePdfView.as_view(), name='signal-pdf-download'),
        path('signals/category/removed',
             SignalCategoryRemovedAfterViewSet.as_view({'get': 'list'}),
             name='signal-category-changed-since'),

        # Search
        path('search', SearchView.as_view({'get': 'list'}), name='elastic-search')
    ])),
]
