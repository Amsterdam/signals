"""
V1 API ViewSet.
"""
from signals.apps.api.v1.views.area import PrivateAreasViewSet, PublicAreasViewSet
from signals.apps.api.v1.views.attachment import (
    PrivateSignalAttachmentsViewSet,
    PublicSignalAttachmentsViewSet
)
from signals.apps.api.v1.views.category import PrivateCategoryViewSet, PublicCategoryViewSet
from signals.apps.api.v1.views.category_removed import SignalCategoryRemovedAfterViewSet
from signals.apps.api.v1.views.csv import PrivateCsvViewSet
from signals.apps.api.v1.views.departments import PrivateDepartmentViewSet
from signals.apps.api.v1.views.expression import PrivateExpressionViewSet
# from signals.apps.api.v1.views.ml_tool_proxy import MlPredictCategoryView  # V1 disabled for now
from signals.apps.api.v1.views.ml_tool_proxy import LegacyMlPredictCategoryView
from signals.apps.api.v1.views.namespace import NamespaceView
from signals.apps.api.v1.views.pdf import GeneratePdfView
from signals.apps.api.v1.views.questions import PublicQuestionViewSet
from signals.apps.api.v1.views.signal import (
    PrivateSignalViewSet,
    PublicSignalListViewSet,
    PublicSignalViewSet,
    SignalPromotedToParentViewSet
)
from signals.apps.api.v1.views.source import PrivateSourcesViewSet
from signals.apps.api.v1.views.status_message_template import StatusMessageTemplatesViewSet
from signals.apps.api.v1.views.stored_signal_filter import StoredSignalFilterViewSet

__all__ = (
    'PublicSignalAttachmentsViewSet',
    'PrivateSignalAttachmentsViewSet',
    'PublicSignalViewSet',
    'PublicSignalListViewSet',
    'PrivateSignalViewSet',
    'SignalCategoryRemovedAfterViewSet',
    'SignalPromotedToParentViewSet',
    'PrivateCategoryViewSet',
    'PrivateCsvViewSet',
    'PublicQuestionViewSet',
    # 'MlPredictCategoryView',  # V1 disabled for now
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
)
