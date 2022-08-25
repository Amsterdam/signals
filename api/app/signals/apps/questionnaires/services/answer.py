# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.core.exceptions import ValidationError as django_validation_error

from signals.apps.questionnaires.fieldtypes import SelectedObject, get_field_type_class


class AnswerService:
    @staticmethod
    def transform_to_extra_property(answer_payload, question):
        """
        Transforms the answer payload to the old "extra_property" style
        """
        if isinstance(question.field_type_class(), SelectedObject):
            extra_property_payload = {}
            if answer_payload['id']:
                extra_property_payload.update({'id': answer_payload['id']})

            if not answer_payload['onMap']:
                extra_property_payload.update({'type': 'not-on-map'})
            else:
                extra_property_payload.update({'type': answer_payload['type']})

            extra_property_payload.update({'location': {'coordinates': answer_payload['coordinates']}})
        else:
            # Default use the answer_payload as is
            extra_property_payload = answer_payload

        return {
            'id': question.analysis_key,
            'label': question.short_label,
            'answer': extra_property_payload,
        }

    @staticmethod
    def validate_answer_payload(answer_payload, question):  # noqa: C901
        # If a question is not required the answer payload must be JSON null,
        # anything else gets the schema check.
        if not question.required and answer_payload is None:
            return answer_payload

        # FieldType subclass schema check
        field_type = question.get_field_type()
        field_type.validate_submission_payload(answer_payload)

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
