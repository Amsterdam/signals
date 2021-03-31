# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
V1 API Serializers.
"""
from signals.apps.api.v1.serializers.attachment import (
    PrivateSignalAttachmentSerializer,
    PublicSignalAttachmentSerializer,
    SignalAttachmentSerializer
)
from signals.apps.api.v1.serializers.category import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PrivateCategorySerializer
)
from signals.apps.api.v1.serializers.departments import (
    PrivateDepartmentSerializerDetail,
    PrivateDepartmentSerializerList
)
from signals.apps.api.v1.serializers.empty import PublicEmptySerializer
from signals.apps.api.v1.serializers.expression import ExpressionContextSerializer
from signals.apps.api.v1.serializers.question import PublicQuestionSerializerDetail
from signals.apps.api.v1.serializers.signal import (
    AbridgedChildSignalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    ReporterContextSignalSerializer,
    SignalGeoSerializer,
    SignalIdListSerializer
)
from signals.apps.api.v1.serializers.signal_history import HistoryHalSerializer
from signals.apps.api.v1.serializers.status_message_template import (
    StateStatusMessageTemplateListSerializer,
    StateStatusMessageTemplateSerializer
)
from signals.apps.api.v1.serializers.stored_signal_filter import StoredSignalFilterSerializer

__all__ = [
    'PublicSignalAttachmentSerializer',
    'PrivateSignalAttachmentSerializer',
    'SignalAttachmentSerializer',
    'StateStatusMessageTemplateListSerializer',
    'StateStatusMessageTemplateSerializer',
    'CategoryHALSerializer',
    'ParentCategoryHALSerializer',
    'HistoryHalSerializer',
    'PrivateDepartmentSerializerDetail',
    'PrivateDepartmentSerializerList',
    'PrivateSignalSerializerDetail',
    'PrivateSignalSerializerList',
    'PublicSignalSerializerDetail',
    'PublicSignalCreateSerializer',
    'ReporterContextSignalSerializer',
    'SignalGeoSerializer',
    'SignalIdListSerializer',
    'StoredSignalFilterSerializer',
    'PrivateCategorySerializer',
    'PublicQuestionSerializerDetail',
    'AbridgedChildSignalSerializer',
    'ExpressionContextSerializer',
    'PublicEmptySerializer'
]
