# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import uuid

from django.contrib.gis.db import models


class QuestionManager(models.Manager):
    def get_by_reference(self, ref):
        """
        Retrieve question key or uuid (either can be the ref).
        """
        from signals.apps.questionnaires.models import Question

        try:
            question_uuid = uuid.UUID(ref)
        except ValueError:
            return Question.objects.get(key=ref)
        else:
            return Question.objects.get(uuid=question_uuid)
