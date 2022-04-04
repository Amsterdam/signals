# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class Boolean(FieldType):
    submission_schema = {'type': 'boolean'}
