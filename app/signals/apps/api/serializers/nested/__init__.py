# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
API nested serializers used in various 'signals.Signal' serializers.
"""

from signals.apps.api.serializers.nested.attachment import _NestedAttachmentModelSerializer
from signals.apps.api.serializers.nested.category import _NestedCategoryModelSerializer
from signals.apps.api.serializers.nested.department import (
    _NestedDepartmentModelSerializer,
    _NestedPublicDepartmentSerializer
)
from signals.apps.api.serializers.nested.location import _NestedLocationModelSerializer
from signals.apps.api.serializers.nested.note import _NestedNoteModelSerializer
from signals.apps.api.serializers.nested.priority import _NestedPriorityModelSerializer
from signals.apps.api.serializers.nested.reporter import _NestedReporterModelSerializer
from signals.apps.api.serializers.nested.status import (
    _NestedPublicStatusModelSerializer,
    _NestedStatusModelSerializer
)
from signals.apps.api.serializers.nested.type import _NestedTypeModelSerializer

__all__ = (
    '_NestedLocationModelSerializer',
    '_NestedStatusModelSerializer',
    '_NestedPublicStatusModelSerializer',
    '_NestedCategoryModelSerializer',
    '_NestedReporterModelSerializer',
    '_NestedPriorityModelSerializer',
    '_NestedNoteModelSerializer',
    '_NestedAttachmentModelSerializer',
    '_NestedTypeModelSerializer',
    '_NestedDepartmentModelSerializer',
    '_NestedPublicDepartmentSerializer',
)
