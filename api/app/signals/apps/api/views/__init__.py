# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from signals.apps.api.views.area import PrivateAreasViewSet, PublicAreasViewSet
from signals.apps.api.views.attachment import (
    PrivateSignalAttachmentsViewSet,
    PublicSignalAttachmentsViewSet
)
from signals.apps.api.views.category import PrivateCategoryViewSet, PublicCategoryViewSet
from signals.apps.api.views.category_removed import SignalCategoryRemovedAfterViewSet
from signals.apps.api.views.csv import PrivateCsvViewSet
from signals.apps.api.views.departments import PrivateDepartmentViewSet
from signals.apps.api.views.expression import PrivateExpressionViewSet
from signals.apps.api.views.ml_tool_proxy import LegacyMlPredictCategoryView
from signals.apps.api.views.namespace import NamespaceView
from signals.apps.api.views.questions import PublicQuestionViewSet
from signals.apps.api.views.signals.private.signal_context import SignalContextViewSet
from signals.apps.api.views.signals.private.signals import PrivateSignalViewSet
from signals.apps.api.views.signals.private.signals_promoted_to_parent import (
    SignalPromotedToParentViewSet
)
from signals.apps.api.views.signals.public.signals import PublicSignalViewSet
from signals.apps.api.views.signals.public.signals_map import PublicSignalMapViewSet
from signals.apps.api.views.source import PrivateSourcesViewSet
from signals.apps.api.views.status_message_template import StatusMessageTemplatesViewSet
from signals.apps.api.views.stored_signal_filter import StoredSignalFilterViewSet

__all__ = (
    'PublicSignalAttachmentsViewSet',
    'PrivateSignalAttachmentsViewSet',
    'PublicSignalMapViewSet',
    'PublicSignalViewSet',
    'PrivateSignalViewSet',
    'SignalCategoryRemovedAfterViewSet',
    'SignalPromotedToParentViewSet',
    'PrivateCategoryViewSet',
    'PrivateCsvViewSet',
    'PublicQuestionViewSet',
    'LegacyMlPredictCategoryView',
    'NamespaceView',
    'PrivateDepartmentViewSet',
    'StatusMessageTemplatesViewSet',
    'StoredSignalFilterViewSet',
    'PublicAreasViewSet',
    'PrivateAreasViewSet',
    'PrivateExpressionViewSet',
    'PrivateSourcesViewSet',
    'PublicCategoryViewSet',
    'SignalContextViewSet',
)
