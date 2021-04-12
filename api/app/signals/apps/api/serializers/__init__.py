# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
V1 API Serializers.
"""
from signals.apps.api.serializers.attachment import (
    PrivateSignalAttachmentSerializer,
    PublicSignalAttachmentSerializer,
    SignalAttachmentSerializer
)
from signals.apps.api.serializers.category import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PrivateCategorySerializer
)
from signals.apps.api.serializers.departments import (
    PrivateDepartmentSerializerDetail,
    PrivateDepartmentSerializerList
)
from signals.apps.api.serializers.expression import ExpressionContextSerializer
from signals.apps.api.serializers.question import PublicQuestionSerializerDetail
from signals.apps.api.serializers.signal import (
    AbridgedChildSignalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalGeoSerializer,
    SignalIdListSerializer
)
from signals.apps.api.serializers.signal_history import HistoryHalSerializer
from signals.apps.api.serializers.status_message_template import (
    StateStatusMessageTemplateListSerializer,
    StateStatusMessageTemplateSerializer
)
from signals.apps.api.serializers.stored_signal_filter import StoredSignalFilterSerializer

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
    'SignalGeoSerializer',
    'SignalIdListSerializer',
    'StoredSignalFilterSerializer',
    'PrivateCategorySerializer',
    'PublicQuestionSerializerDetail',
    'AbridgedChildSignalSerializer',
    'ExpressionContextSerializer',
]
