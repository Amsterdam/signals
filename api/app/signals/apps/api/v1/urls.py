from django.conf import settings
from django.urls import include, path, re_path

from signals.apps.api.v1.routers import SignalsRouterVersion1
from signals.apps.api.v1.views import (  # MLPredictCategoryView,  # V1 disabled for now
    GeneratePdfView,
    NamespaceView,
    PrivateAreasViewSet,
    PrivateCategoryViewSet,
    PrivateCsvViewSet,
    PrivateDepartmentViewSet,
    PrivateExpressionViewSet,
    PrivateSignalAttachmentsViewSet,
    PrivateSignalViewSet,
    PrivateSourcesViewSet,
    PublicAreasViewSet,
    PublicCategoryViewSet,
    PublicQuestionViewSet,
    PublicSignalAttachmentsViewSet,
    PublicSignalListViewSet,
    PublicSignalViewSet,
    SignalCategoryRemovedAfterViewSet,
    SignalPromotedToParentViewSet,
    StatusMessageTemplatesViewSet,
    StoredSignalFilterViewSet
)
from signals.apps.feedback.views import FeedbackViewSet, StandardAnswerViewSet
from signals.apps.search.views import SearchView
from signals.apps.users.v1.views import PermissionViewSet, RoleViewSet, UserViewSet

# Public API
public_router = SignalsRouterVersion1()
public_router.register(r'public/signals', PublicSignalViewSet, basename='public-signals')
public_router.register(r'public/feedback/standard_answers', StandardAnswerViewSet, basename='feedback-standard-answers')
public_router.register(r'public/feedback/forms', FeedbackViewSet, basename='feedback-forms')
public_router.register(r'public/areas', PublicAreasViewSet, basename='public-areas')

public_categories = public_router.register(r'public/terms/categories', PublicCategoryViewSet,
                                           basename='public-maincategory')
public_categories.register(r'sub_categories', PublicCategoryViewSet, basename='public-subcategory',
                           parents_query_lookups=['parent__slug'])

if settings.ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT:
    public_router.register(r'public/map-signals', PublicSignalListViewSet, basename='public-list-signals')

# Private API
private_router = SignalsRouterVersion1()
private_signals = private_router.register(r'private/signals', PrivateSignalViewSet, basename='private-signals')
private_signals.register(r'attachments', PrivateSignalAttachmentsViewSet, basename='private-signals-attachments',
                         parents_query_lookups=['_signal__pk'])
private_router.register(r'private/me/filters', StoredSignalFilterViewSet, basename='stored-signal-filters')
private_router.register(r'private/users', UserViewSet, basename='user')
private_router.register(r'private/roles', RoleViewSet, basename='group')
private_router.register(r'private/permissions', PermissionViewSet, basename='permission')
private_router.register(r'private/departments', PrivateDepartmentViewSet, basename='department')
private_router.register(r'private/categories', PrivateCategoryViewSet, basename='private-category')
private_router.register(r'private/areas', PrivateAreasViewSet, basename='private-areas')
private_router.register(r'private/expressions', PrivateExpressionViewSet, basename='private-expression')
private_router.register(r'private/sources', PrivateSourcesViewSet, basename='private-sources')
private_router.register(r'private/csv', PrivateCsvViewSet, basename='private-csv')


# Combined API
base_router = SignalsRouterVersion1()
base_router.registry.extend(public_router.registry)
base_router.registry.extend(private_router.registry)

urlpatterns = [
    # The base routes of the API
    path('v1/', include(base_router.urls)),

    # Used for namespacing SIA, a HAL standard
    re_path(r'v1/relations/?$', NamespaceView.as_view(), name='signal-namespace'),

    # Public additions
    path('v1/public/', include([
        re_path(r'signals/(?P<signal_id>[-\w]+)/attachments/?$',
                PublicSignalAttachmentsViewSet.as_view({'post': 'create'}), name='public-signals-attachments'),
        re_path(r'questions/?$', PublicQuestionViewSet.as_view({'get': 'list'}), name='question-detail'),
    ])),

    # Private additions
    path('v1/private/', include([
        # Returns the details of the currently logged in user
        re_path('me/?$', UserViewSet.as_view({'get': 'me'}), name='auth-me'),

        # Get/Replace the status message templates per category
        re_path(r'terms/categories/(?P<slug>[-\w]+)/status-message-templates/?$',
                StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
                name='private-status-message-templates-parent'),
        re_path(r'terms/categories/(?P<slug>[-\w]+)/sub_categories/(?P<sub_slug>[-\w]+)/status-message-templates/?$',
                StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
                name='private-status-message-templates-child'),

        # Additional Signals endpoints
        re_path(r'signals/(?P<pk>\d+)/pdf/?$', GeneratePdfView.as_view(), name='signal-pdf-download'),
        re_path(r'signals/category/removed/?$', SignalCategoryRemovedAfterViewSet.as_view({'get': 'list'}),
                name='signal-category-changed-since'),

        re_path(r'signals/promoted/parent/?$', SignalPromotedToParentViewSet.as_view({'get': 'list'}),
                name='signal-became-parent-since'),

        # Search
        re_path('search/?$', SearchView.as_view({'get': 'list'}), name='elastic-search'),

    ])),
]
