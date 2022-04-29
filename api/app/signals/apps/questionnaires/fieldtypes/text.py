# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class PlainText(FieldType):
    submission_schema = {'type': 'string'}


class Email(FieldType):
    submission_schema = {'type': 'string', 'format': 'email'}
