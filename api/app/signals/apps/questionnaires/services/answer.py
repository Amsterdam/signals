# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.core.exceptions import ValidationError as django_validation_error

from signals.apps.questionnaires.fieldtypes import get_field_type_class


class AnswerService:
    @staticmethod
    def validate_answer_payload(answer_payload, question):  # noqa: C901
        # If a question is not required the answer payload must be JSON null,
        # anything else gets the schema check.
        if not question.required and answer_payload is None:
            return answer_payload

        # FieldType subclass schema check
        field_type_class = get_field_type_class(question)
        field_type_class().validate_submission_payload(answer_payload)

        # If a questions has pre-defined answers (see the Choice model), the
        # answer payload should match one of these predefined answers.
        if not question.enforce_choices:
            return answer_payload

        if valid_payloads := question.choices.values_list('payload', flat=True):
            for valid_payload in valid_payloads:
                if answer_payload == valid_payload:
                    return answer_payload
            else:
                msg = 'Submitted answer does not match one of the pre-defined answers.'
                raise django_validation_error(msg)
