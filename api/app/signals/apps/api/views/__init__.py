# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
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
# from signals.apps.api.views.ml_tool_proxy import MlPredictCategoryView  # disabled for now
from signals.apps.api.views.ml_tool_proxy import LegacyMlPredictCategoryView
from signals.apps.api.views.namespace import NamespaceView
from signals.apps.api.views.pdf import GeneratePdfView
from signals.apps.api.views.questions import PublicQuestionViewSet
from signals.apps.api.views.signal import (
    PrivateSignalViewSet,
    PublicSignalMapViewSet,
    PublicSignalViewSet,
    SignalPromotedToParentViewSet
)
from signals.apps.api.views.signal_context import SignalContextViewSet
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
    # 'MlPredictCategoryView',  # disabled for now
    'LegacyMlPredictCategoryView',
    'NamespaceView',
    'GeneratePdfView',
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
