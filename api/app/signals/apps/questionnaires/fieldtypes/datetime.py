# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class Date(FieldType):
    submission_schema = {'type': 'string', 'format': 'date'}


class Time(FieldType):
    submission_schema = {'type': 'string', 'format': 'time'}


class DateTime(FieldType):
    submission_schema = {'type': 'string', 'format': 'date-time'}
