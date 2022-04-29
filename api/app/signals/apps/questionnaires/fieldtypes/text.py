# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from signals.apps.questionnaires.fieldtypes.base import FieldType


class PlainText(FieldType):
    submission_schema = {'type': 'string'}


class Email(FieldType):
    submission_schema = {'type': 'string', 'format': 'email'}


class DutchTelephoneNumber(FieldType):
    verbose_name = 'Telephone number (NL)'
    submission_schema = {'type': 'string',
                         'regex': '^(?:0|(?:\+|00) ?31 ?)(?:(?:[1-9] ?(?:[0-9] ?){8})|(?:6 ?-? ?[1-9] ?(?:[0-9] ?){7})|(?:[1,2,3,4,5,7,8,9]\d ?-? ?[1-9] ?(?:[0-9] ?){6})|(?:[1,2,3,4,5,7,8,9]\d{2} ?-? ?[1-9] ?(?:[0-9] ?){5}))$'}  # noqa
