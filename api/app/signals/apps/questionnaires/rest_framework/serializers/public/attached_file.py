# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from datapunt_api.rest import HALSerializer

from signals.apps.questionnaires.models.attached_file import AttachedFile


class NestedPublicAttachedFileSerializer(HALSerializer):
    model = AttachedFile
    fields = ('id', )
