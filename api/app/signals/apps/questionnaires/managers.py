# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from django.contrib.gis.db import models
from django.db.models import DateTimeField, ExpressionWrapper, F, Q
from django.db.models.functions import Now


class QuestionManager(models.Manager):
    def get_by_reference(self, ref):
        """
        Retrieve question key or uuid (either can be the ref).
        """
        from signals.apps.questionnaires.models import Question

        if ref is None:
            msg = 'Cannot get Question instance for ref=None'
            raise Question.DoesNotExist(msg)

        if ref == 'submit':
            question, _ = Question.objects.get_or_create(
                key='submit',
                field_type='submit',
                label='Verstuur',
                short_label='Verstuur',
                required=True
            )
            return question

        try:
            question_uuid = uuid.UUID(ref)
        except (ValueError, TypeError):
            return Question.objects.get(key=ref)
        else:
            return Question.objects.get(uuid=question_uuid)


class QuestionnaireManager(models.Manager):
    def active(self):
        """
        Returns only Questionnaires with the is_active set to True
        """
        return self.get_queryset().filter(is_active=True)


class SessionManager(models.Manager):
    def retrieve_valid_sessions(self):
        """
        Returns a queryset containing Sessions that fit one of the following conditions:

        * The submit_before is set and is still valid
        * The submit_before is NOT set, the Session is in use and the started_at + duration is still valid
        * The submit_before is NOT set and the Session is NOT in use

        And all of these conditions must only contain Sessions that are not frozen. Frozen sessions cannot be edited!
        """
        queryset = self.get_queryset()
        return queryset.annotate(
            # Calculate the submit before based on the started_at + duration
            submit_before_based_on_duration=ExpressionWrapper(
                F('started_at') + F('duration'),
                output_field=DateTimeField()
            )
        ).filter(
            (
                # All sessions that have a submit_before that has not yet passed
                (Q(submit_before__isnull=False) & Q(submit_before__gt=Now())) |
                # All sessions that do not have a submit_before but where the created_at + duration has not yet passed
                (Q(submit_before__isnull=True) & Q(submit_before_based_on_duration__gt=Now())) |
                # All sessions that have no submit_before and has not yet been answered
                (Q(submit_before__isnull=True) & Q(submit_before_based_on_duration__isnull=True))
            ),
            # Frozen session are not editable anymore
            frozen=False,
        ).all()
