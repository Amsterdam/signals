"""
API V1 nested serializers used in various 'signals.Signal' serializers.
"""

from signals.apps.api.v1.serializers.nested.attachment import _NestedAttachmentModelSerializer
from signals.apps.api.v1.serializers.nested.category import _NestedCategoryModelSerializer
from signals.apps.api.v1.serializers.nested.department import _NestedDepartmentModelSerializer
from signals.apps.api.v1.serializers.nested.location import _NestedLocationModelSerializer
from signals.apps.api.v1.serializers.nested.note import _NestedNoteModelSerializer
from signals.apps.api.v1.serializers.nested.priority import _NestedPriorityModelSerializer
from signals.apps.api.v1.serializers.nested.reporter import _NestedReporterModelSerializer
from signals.apps.api.v1.serializers.nested.signal_split import _NestedSplitSignalSerializer
from signals.apps.api.v1.serializers.nested.status import (
    _NestedPublicStatusModelSerializer,
    _NestedStatusModelSerializer
)
from signals.apps.api.v1.serializers.nested.type import _NestedTypeModelSerializer

__all__ = (
    '_NestedLocationModelSerializer',
    '_NestedStatusModelSerializer',
    '_NestedPublicStatusModelSerializer',
    '_NestedCategoryModelSerializer',
    '_NestedReporterModelSerializer',
    '_NestedPriorityModelSerializer',
    '_NestedNoteModelSerializer',
    '_NestedAttachmentModelSerializer',
    '_NestedSplitSignalSerializer',
    '_NestedTypeModelSerializer',
    '_NestedDepartmentModelSerializer',
)
