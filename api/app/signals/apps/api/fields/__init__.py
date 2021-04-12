# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
API V1 Fields.
"""
from signals.apps.api.fields.attachment import (
    PrivateSignalAttachmentLinksField,
    PublicSignalAttachmentLinksField
)
from signals.apps.api.fields.category import (
    CategoryHyperlinkedIdentityField,
    CategoryHyperlinkedRelatedField,
    PrivateCategoryHyperlinkedIdentityField
)
from signals.apps.api.fields.note import NoteHyperlinkedIdentityField
from signals.apps.api.fields.signal import (
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    PublicSignalLinksField
)
from signals.apps.api.fields.stored_signal_filter import StoredSignalFilterLinksField

__all__ = [
    'CategoryHyperlinkedIdentityField',
    'CategoryHyperlinkedRelatedField',
    'NoteHyperlinkedIdentityField',
    'PrivateSignalLinksFieldWithArchives',
    'PrivateSignalLinksField',
    'PublicSignalLinksField',
    'PublicSignalAttachmentLinksField',
    'PrivateSignalAttachmentLinksField',
    'StoredSignalFilterLinksField',
    'PrivateCategoryHyperlinkedIdentityField',
]
