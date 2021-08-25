# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.questionnaires.admin.admins import (
    QuestionAdmin,
    QuestionGraphAdmin,
    QuestionnaireAdmin,
    SessionAdmin
)
from signals.apps.questionnaires.models import Question, QuestionGraph, Questionnaire, Session

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(QuestionGraph, QuestionGraphAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Session, SessionAdmin)
