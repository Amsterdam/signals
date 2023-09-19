# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.conf import settings
from django.urls import include, path, re_path

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.api.views import (
    LegacyMlPredictCategoryView,
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
    PublicSignalMapViewSet,
    PublicSignalViewSet,
    SignalCategoryRemovedAfterViewSet,
    SignalContextViewSet,
    SignalPromotedToParentViewSet,
    StatusMessageTemplatesViewSet,
    StoredSignalFilterViewSet
)
from signals.apps.api.views.category import PrivateCategoryIconViewSet
from signals.apps.api.views.email_verification import EmailVerificationView
from signals.apps.api.views.signals.private.signal_reporters import PrivateSignalReporterViewSet
from signals.apps.api.views.status_message import (
    StatusMessagesCategoryPositionViewSet,
    StatusMessagesViewSet
)
from signals.apps.api.views.translations import (
    PrivateCreateI18NextTranslationFileView,
    PublicRetrieveI18NextTranslationFileView
)
from signals.apps.search.rest_framework.views import SearchView, StatusMessageSearchView
from signals.apps.users.rest_framework.views import (
    AutocompleteUsernameListView,
    LoggedInUserView,
    PermissionViewSet,
    RoleViewSet,
    UserViewSet
)

# Public API
public_router = SignalsRouter()
public_router.register(r'public/signals', PublicSignalViewSet, basename='public-signals')
public_router.register(r'public/areas', PublicAreasViewSet, basename='public-areas')
public_categories = public_router.register(r'public/terms/categories', PublicCategoryViewSet,
                                           basename='public-maincategory')
public_categories.register(r'sub_categories', PublicCategoryViewSet, basename='public-subcategory',
                           parents_query_lookups=['parent__slug'])

if settings.ENABLE_PUBLIC_GEO_SIGNAL_ENDPOINT:
    public_router.register(r'public/map-signals', PublicSignalMapViewSet, basename='public-list-signals')

# Private API
private_router = SignalsRouter()
private_signals = private_router.register(r'private/signals', PrivateSignalViewSet, basename='private-signals')
private_signals.register(r'attachments', PrivateSignalAttachmentsViewSet, basename='private-signals-attachments',
                         parents_query_lookups=['_signal__pk'])
private_signals.register(r'reporters', PrivateSignalReporterViewSet, basename='private-signals-reporters',
                         parents_query_lookups=['_signal_id'])

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
private_router.register(r'private/status-messages', StatusMessagesViewSet, basename='status-message')
private_router.register(r'private/status-messages/category/(?P<category_id>\d+)',
                        StatusMessagesCategoryPositionViewSet, basename='status-message-category-position')

# Combined API
base_router = SignalsRouter()
base_router.registry.extend(public_router.registry)
base_router.registry.extend(private_router.registry)

urlpatterns = [
    # Status message search
    re_path(r'v1/private/status-messages/search/?$', StatusMessageSearchView.as_view(), name='status-message-search'),

    # Legacy prediction proxy endpoint, still needed
    path('category/prediction', LegacyMlPredictCategoryView.as_view(), name='ml-tool-predict-proxy'),

    # The base routes of the API
    path('v1/', include(base_router.urls)),

    # Used for namespacing SIA, a HAL standard
    re_path(r'v1/relations/?$', NamespaceView.as_view(), name='signal-namespace'),

    # Public additions
    path('v1/public/', include([
        re_path(r'signals/(?P<uuid>[-\w]+)/attachments/?$',
                PublicSignalAttachmentsViewSet.as_view({'post': 'create'}), name='public-signals-attachments'),
        re_path(r'questions/?$', PublicQuestionViewSet.as_view({'get': 'list'}), name='question-detail'),
        path('reporter/verify-email', EmailVerificationView.as_view(), name='email-verification'),
        path('translations.json', PublicRetrieveI18NextTranslationFileView.as_view(),
             name='public-i18next-latest-translations'),

    ])),

    # Private additions
    path('v1/private/', include([
        # Returns the details of the currently logged in user
        re_path('me/?$', LoggedInUserView.as_view(), name='auth-me'),

        # Get/Replace the status message templates per category
        re_path(r'terms/categories/(?P<slug>[-\w]+)/status-message-templates/?$',
                StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
                name='private-status-message-templates-parent'),
        re_path(r'terms/categories/(?P<slug>[-\w]+)/sub_categories/(?P<sub_slug>[-\w]+)/status-message-templates/?$',
                StatusMessageTemplatesViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
                name='private-status-message-templates-child'),

        # Additional Signals endpoints
        re_path(r'signals/category/removed/?$', SignalCategoryRemovedAfterViewSet.as_view({'get': 'list'}),
                name='signal-category-changed-since'),

        re_path(r'signals/promoted/parent/?$', SignalPromotedToParentViewSet.as_view({'get': 'list'}),
                name='signal-became-parent-since'),

        # Search
        re_path('search/?$', SearchView.as_view({'get': 'list'}), name='elastic-search'),

        # Used for autocompletion
        path('autocomplete/', include([
            re_path('usernames/?$', AutocompleteUsernameListView.as_view(), name='autocomplete-usernames'),
        ])),

        # Signal context
        re_path(r'signals/(?P<pk>\d+)/context/?$', SignalContextViewSet.as_view({'get': 'retrieve'}),
                name='private-signal-context'),
        re_path(r'signals/(?P<pk>\d+)/context/reporter/?$', SignalContextViewSet.as_view({'get': 'reporter'}),
                name='private-signal-context-reporter'),
        re_path(r'signals/(?P<pk>\d+)/context/near/geography/?$', SignalContextViewSet.as_view({'get': 'near'}),
                name='private-signal-context-near-geography'),

        re_path(r'categories/(?P<category_id>\d+)/icon',
                PrivateCategoryIconViewSet.as_view({'get': 'retrieve',
                                                    'put': 'update',
                                                    'patch': 'update',
                                                    'delete': 'destroy'}),
                name='private-category-icon'),

        path('translations/', PrivateCreateI18NextTranslationFileView.as_view(), name='private-i18next-translations')
    ])),

    # Feedback
    path('v1/', include('signals.apps.feedback.urls')),
    # Reporting
    path('v1/', include('signals.apps.reporting.urls')),
    # Questionnaires
    path('v1/', include('signals.apps.questionnaires.urls')),
]

if 'MY_SIGNALS_ENABLED' in settings.FEATURE_FLAGS and settings.FEATURE_FLAGS['MY_SIGNALS_ENABLED']:
    urlpatterns += [
        # My Signals
        path('v1/', include('signals.apps.my_signals.urls')),
    ]
