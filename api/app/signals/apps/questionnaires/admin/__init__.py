# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.questionnaires.admin.admins import (
    ChoiceAdmin,
    QuestionAdmin,
    QuestionGraphAdmin,
    QuestionnaireAdmin,
    SessionAdmin
)
from signals.apps.questionnaires.models import (
    Choice,
    Question,
    QuestionGraph,
    Questionnaire,
    Session
)

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(QuestionGraph, QuestionGraphAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Choice, ChoiceAdmin)
