# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2025 Gemeente Amsterdam
import pytz
from django.conf import settings
from django.dispatch import Signal as DjangoSignal
from django.utils import timezone

from signals.apps.feedback.models import Feedback
from signals.apps.history.models import Log
from signals.apps.questionnaires.models import Questionnaire, Session
from signals.apps.signals.models import (
    CategoryAssignment,
    Location,
    Note,
    Priority,
    Signal,
    SignalDepartments,
    SignalUser,
    Status
)
from signals.apps.signals.models import Type as _Type

# When a relevant model in relation to the Signal model is created/updated,
# the Signal model itself should be updated.
# This to give more precise info on which Signal has the latest activity.
signal_update_requested = DjangoSignal()


class SignalLogService:
    @staticmethod
    def log_create_initial(signal: Signal) -> None:
        if signal.is_child:
            # We cannot create a GenericRelation on the Signal model because the naming will clash with the ForeignKey
            # `_signal` defined on the Log model. So for now Log rules for a specific Signal are created as seen here:
            Log.objects.create(
                action=Log.ACTION_CREATE,
                extra=str(signal.id),
                object=signal,
                created_by=None,
                created_at=signal.created_at,
                _signal=signal.parent,
            )

            # Update the parent Signal so that it's updated_at column and history are aligned.
            # Without this, there will be no update if there is no note added to the deelmelding action
            if signal.parent:
                signal_update_requested.send(sender=Signal, signal_instance=signal.parent)

        if signal.location:
            SignalLogService.log_update_location(signal.location)

        if signal.status:
            SignalLogService.log_update_status(signal.status)

        if signal.category_assignment:
            SignalLogService.log_update_category_assignment(signal.category_assignment)

        if signal.priority:
            SignalLogService.log_update_priority(signal.priority)

        if signal.type_assignment:
            SignalLogService.log_update_type(signal.type_assignment)

    @staticmethod
    def log_create_note(note: Note) -> None:
        if not isinstance(note, Note):
            return

        note.history_log.create(
            action=Log.ACTION_CREATE,
            description=note.text,
            extra='Notitie toegevoegd',
            created_by=note.created_by,
            created_at=note.created_at,
            _signal=note._signal,
        )

    @staticmethod
    def log_update_category_assignment(category_assignment: CategoryAssignment) -> None:
        if not isinstance(category_assignment, CategoryAssignment):
            return

        if category_assignment.category.slo.exists() and category_assignment._signal.categories.count() == 1:
            _slo = category_assignment.category.slo.first()
            if _slo:
                _slo.history_log.create(
                    action=Log.ACTION_UPDATE,
                    description=category_assignment.stored_handling_message,
                    created_by=category_assignment.created_by,
                    created_at=category_assignment.created_at,
                    _signal=category_assignment._signal,
                )

        category_assignment.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=category_assignment.category.name,
            created_by=category_assignment.created_by,
            created_at=category_assignment.created_at,
            _signal=category_assignment._signal,
        )

    @staticmethod
    def log_update_location(location: Location) -> None:
        if not isinstance(location, Location):
            return

        location.history_log.create(
            action=Log.ACTION_UPDATE,
            extra='Locatie gewijzigd',
            created_by=location.created_by,
            created_at=location.created_at,
            _signal=location._signal,
        )

    @staticmethod
    def log_update_priority(priority: Priority) -> None:
        if not isinstance(priority, Priority):
            return

        priority.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=priority.priority,
            created_by=priority.created_by,
            created_at=priority.created_at,
            _signal=priority._signal,
        )

    @staticmethod
    def log_update_status(status: Status) -> None:
        if not isinstance(status, Status):
            return

        status.history_log.create(
            action=Log.ACTION_UPDATE,
            description=status.text,
            extra=status.state,
            created_by=status.created_by,
            created_at=status.created_at,
            _signal=status._signal,
        )

    @staticmethod
    def log_update_type(_type: _Type) -> None:
        if not isinstance(_type, _Type):
            return

        _type.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=_type.name,
            created_by=_type.created_by,
            created_at=_type.created_at,
            _signal=_type._signal,
        )

    @staticmethod
    def log_update_user_assignment(user_assignment: SignalUser) -> None:
        if not isinstance(user_assignment, SignalUser):
            return

        log_extra = user_assignment.user.email if user_assignment.user else None
        user_assignment.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=log_extra,
            created_by=user_assignment.created_by,
            created_at=user_assignment.created_at,
            _signal=user_assignment._signal,
        )

    @staticmethod
    def log_update_signal_departments(signal_departments: SignalDepartments) -> None:
        if not isinstance(signal_departments, SignalDepartments):
            return

        extra = ', '.join(signal_departments.departments.values_list('code', flat=True))
        signal_departments.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=extra,
            description=None,
            created_by=signal_departments.created_by,
            created_at=signal_departments.created_at,
            _signal=signal_departments._signal,
        )

    @staticmethod
    def log_receive_feedback(feedback: Feedback) -> None:
        if not isinstance(feedback, Feedback):
            return

        if feedback.submitted_at is None:
            # No feedback was submitted, so we don't log anything
            return

        feedback.history_log.create(
            action=Log.ACTION_CREATE,
            extra='Feedback ontvangen',
            description=feedback.get_description(),
            created_by=None,
            created_at=feedback.submitted_at,
            _signal=feedback._signal,
        )

        if feedback._signal:
            signal_update_requested.send(sender=Feedback, signal_instance=feedback._signal)

    @staticmethod
    def log_external_reaction_received(session: Session, reaction: str) -> None:
        if not isinstance(session, Session):
            return

        if session.questionnaire.flow != Questionnaire.FORWARD_TO_EXTERNAL:
            return

        if not session.frozen:
            return

        tz = pytz.timezone(settings.TIME_ZONE)

        when = 'onbekend'
        if session._signal_status:
            when = session._signal_status.created_at.astimezone(tz).strftime('%d-%m-%Y %H:%M')
        description = f'Toelichting externe behandelaar op vraag van {when} {reaction}'

        session.history_log.create(
            action=Log.ACTION_RECEIVE,
            description=description,
            created_by=None,
            created_at=timezone.now(),
            _signal=session._signal,
        )

        if session._signal:
            signal_update_requested.send(sender=Session, signal_instance=session._signal)

    @staticmethod
    def log_external_reaction_not_received(session: Session) -> None:
        if not isinstance(session, Session):
            return

        if session.questionnaire.flow != Questionnaire.FORWARD_TO_EXTERNAL:
            return

        # Log is created just before invalidating the session, hence check that it is not yet invalidated.
        if session.frozen or session.invalidated:
            return

        when = 'onbekend'
        if session._signal_status:
            when = session._signal_status.created_at.strftime('%d-%m-%Y %H:%M')

        description = f'Geen toelichting ontvangen van externe behandelaar op vraag van {when}'

        session.history_log.create(
            action=Log.ACTION_NOT_RECEIVED,
            description=description,
            created_by=None,
            created_at=timezone.now(),
            _signal=session._signal,
        )

        if session._signal:
            signal_update_requested.send(sender=Session, signal_instance=session._signal)
