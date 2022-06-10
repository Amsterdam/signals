# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin

from signals.apps.signals.admin.area import AreaAdmin
from signals.apps.signals.admin.category import CategoryAdmin, StatusMessageTemplatesAdmin
from signals.apps.signals.admin.deleted_signals import DeletedSignalAdmin
from signals.apps.signals.admin.department import DepartmentAdmin
from signals.apps.signals.admin.expression import (
    ExpressionAdmin,
    ExpressionContextAdmin,
    ExpressionTypeAdmin,
    RoutingExpressionAdmin
)
from signals.apps.signals.admin.question import QuestionAdmin
from signals.apps.signals.admin.signal import SignalAdmin
from signals.apps.signals.admin.source import SourceAdmin
from signals.apps.signals.models import (
    Area,
    Category,
    DeletedSignal,
    Department,
    Expression,
    ExpressionContext,
    ExpressionType,
    Question,
    RoutingExpression,
    Signal,
    Source,
    StatusMessageTemplate
)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(StatusMessageTemplate, StatusMessageTemplatesAdmin)
admin.site.register(Signal, SignalAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(RoutingExpression, RoutingExpressionAdmin)
admin.site.register(Expression, ExpressionAdmin)
admin.site.register(ExpressionType, ExpressionTypeAdmin)
admin.site.register(ExpressionContext, ExpressionContextAdmin)
admin.site.register(DeletedSignal, DeletedSignalAdmin)
