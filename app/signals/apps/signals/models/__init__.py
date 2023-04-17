# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from signals.apps.signals.models.area import Area, AreaType
from signals.apps.signals.models.attachment import Attachment
from signals.apps.signals.models.buurt import Buurt
from signals.apps.signals.models.category import Category
from signals.apps.signals.models.category_assignment import CategoryAssignment
from signals.apps.signals.models.category_departments import CategoryDepartment
from signals.apps.signals.models.category_question import CategoryQuestion
from signals.apps.signals.models.deleted_signal import DeletedSignal
from signals.apps.signals.models.department import Department
from signals.apps.signals.models.expression import Expression, ExpressionContext, ExpressionType
from signals.apps.signals.models.location import (
    STADSDEEL_AMSTERDAMSE_BOS,
    STADSDEEL_CENTRUM,
    STADSDEEL_NIEUWWEST,
    STADSDEEL_NOORD,
    STADSDEEL_OOST,
    STADSDEEL_WEESP,
    STADSDEEL_WEST,
    STADSDEEL_WESTPOORT,
    STADSDEEL_ZUID,
    STADSDEEL_ZUIDOOST,
    STADSDELEN,
    Location
)
from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.models.note import Note
from signals.apps.signals.models.priority import Priority
from signals.apps.signals.models.question import Question
from signals.apps.signals.models.reporter import Reporter
from signals.apps.signals.models.routing_expression import RoutingExpression
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.models.signal_departments import SignalDepartments
from signals.apps.signals.models.signal_user import SignalUser
from signals.apps.signals.models.slo import ServiceLevelObjective
from signals.apps.signals.models.source import Source
from signals.apps.signals.models.status import Status
from signals.apps.signals.models.status_message import StatusMessage, StatusMessageCategory
from signals.apps.signals.models.status_message_template import StatusMessageTemplate
from signals.apps.signals.models.stored_signal_filter import StoredSignalFilter
from signals.apps.signals.models.type import Type

# Satisfy Flake8 (otherwise complaints about unused imports):
__all__ = [
    'Area',
    'AreaType',
    'Attachment',
    'Buurt',
    'Category',
    'CategoryAssignment',
    'CategoryDepartment',
    'CategoryQuestion',
    'Department',
    'ExpressionType',
    'ExpressionContext',
    'Expression',
    'SignalDepartments',
    'SignalUser',
    'STADSDEEL_AMSTERDAMSE_BOS',
    'STADSDEEL_CENTRUM',
    'STADSDEEL_NIEUWWEST',
    'STADSDEEL_NOORD',
    'STADSDEEL_OOST',
    'STADSDEEL_WEESP',
    'STADSDEEL_WEST',
    'STADSDEEL_WESTPOORT',
    'STADSDEEL_ZUID',
    'STADSDEEL_ZUIDOOST',
    'STADSDELEN',
    'Location',
    'CreatedUpdatedModel',
    'Note',
    'Question',
    'Priority',
    'Reporter',
    'Signal',
    'ServiceLevelObjective',
    'Source',
    'Status',
    'StatusMessageTemplate',
    'StoredSignalFilter',
    'Type',
    'RoutingExpression',
    'DeletedSignal',
    'StatusMessage',
    'StatusMessageCategory',
]
